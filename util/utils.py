import sys
import getpass
import math
import os
import traceback
from datetime import datetime, timedelta
import hashlib
import matplotlib

###########################################################
# GLOBAL FIELDS
DATE_FORMAT_YYYY_MM_DD = '%Y-%m-%d'
DATE_FORMAT_HH_MM_SS = '%H:%M:%S'
DATE_FORMAT_YYYY_MM_DD_HH_MM_SS = f'{DATE_FORMAT_YYYY_MM_DD} {DATE_FORMAT_HH_MM_SS}'

###########################################################
# Global Output Offset Param
output_day_offset: int = 0


def gct(raw: bool = False) -> [str, datetime]:
    n = datetime.now()
    if raw:
        return n
    return n.strftime(DATE_FORMAT_YYYY_MM_DD_HH_MM_SS)


def current_date_seed() -> int:
    formatted_date = date_today_formatted()
    h = string_to_deterministic_hash(data=formatted_date)
    return int(math.fabs(float(h)))


def format_exception(exception: Exception) -> [str, [str]]:
    description = str(exception.__class__.__name__) + ': "' + str(exception) + '"'

    stacktrace_lines = []
    tb = traceback.TracebackException.from_exception(exception)
    for line in tb.stack:
        stacktrace_lines.append(str(line))

    return description, stacktrace_lines


def calculate_reading_time(text, average_wpm=250):
    words = text.split()
    word_count = len(words)
    time_minutes = word_count / average_wpm
    time_seconds = time_minutes * 60
    return time_seconds


def format_time(time_code: int) -> str:
    hours = time_code // 3600
    minutes = (time_code % 3600) // 60
    seconds = time_code % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def get_username():
    user = None
    tmp_user = None
    try:
        tmp_user = os.environ.get('USER')
    except Exception as e:
        # silently fail
        pass
    if tmp_user is not None and user is not None:
        user = tmp_user

    tmp_user = None
    try:
        tmp_user = os.environ.get('USERNAME')
    except Exception as e:
        # silently fail
        pass
    if tmp_user is not None and user is not None:
        user = tmp_user

    tmp_user = None
    try:
        tmp_user = getpass.getuser()
    except Exception as e:
        # silently fail
        pass
    if tmp_user is not None and user is not None:
        user = tmp_user

    tmp_user = None
    try:
        tmp_user = os.getlogin()
    except Exception as e:
        # silently fail
        pass
    if tmp_user is not None and user is not None:
        user = tmp_user

    if user is None:
        user = '<unknown>'

    user = str(user)
    return user


def remove_quotations(text: str) -> str:
    return text.strip().rstrip('"').rstrip("'").lstrip('"').lstrip("'").strip()


def is_windows_system() -> bool:
    return os.name == 'nt'


def date_today(apply_offset: bool = True) -> datetime:
    today: datetime = datetime.today()

    if apply_offset:
        global output_day_offset
        today = today + timedelta(days=output_day_offset)

    return today


def date_today_formatted(apply_offset: bool = True) -> str:
    today = date_today(apply_offset=apply_offset)
    formatted_date = today.strftime(DATE_FORMAT_YYYY_MM_DD)
    return formatted_date


def string_to_deterministic_hash(data: str) -> int:
    data = str(data).strip()
    hash_object = hashlib.md5()
    hash_object.update(data.encode(encoding='utf-8'))
    hash_bytes = hash_object.digest()
    hash_integer = int.from_bytes(hash_bytes, byteorder='big')
    return hash_integer


# Function to determine the text color based on the background color
def get_dynamic_text_color(background_color) -> str:
    r, g, b = matplotlib.colors.to_rgb(background_color)
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    if brightness > 0.5:
        return 'black'
    else:
        return 'white'


def chat_gpt_api_key_printable(api_key: str) -> str:
    assert api_key is not None

    offset = math.ceil(len(api_key) * 0.075)
    head = api_key[:offset].strip()
    tail = api_key[offset * -1:].strip()

    return f'{head} ... {tail}'


def format_ms(milliseconds: int) -> str:
    milliseconds = int(milliseconds)

    seconds = milliseconds / 1000
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"


def print_progress_bar(iteration: int,
                       total: int,
                       tokens_session: int,
                       tokens_total: int,
                       bar_length: int = 50,
                       eta_text: str = None):
    percent = "{0:.1f}".format(100 * (float(iteration) / float(total)))
    filled_length = int(bar_length * iteration // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    total_length = len(str(total))
    iteration_str = f"{iteration:>{total_length}}"

    progress_text = f"{iteration_str}/{total}"
    out_text = f'\r{progress_text} |{bar}| {percent}%'

    token_text = ''
    if iteration >= total:
        current_date_time = datetime.now()
        formatted_date_time = current_date_time.strftime('%Y.%m.%d %H:%M:%S')
        out_text = out_text + ' Finished: ' + str(formatted_date_time)
        token_text = str(tokens_total)
    elif eta_text is not None:
        out_text = out_text + ' ETA: ' + eta_text
        token_text = str(tokens_session) + '|' + str(tokens_total)

    out_text = out_text + ' [' + token_text + ' tokens]'

    sys.stdout.write(out_text)
    sys.stdout.flush()
