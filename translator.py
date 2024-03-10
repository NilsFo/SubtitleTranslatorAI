import argparse
import sys
import time

import openai.error
import pycountry

import numpy as np
import gpt_model_interface
import subtitles
from util import log, utils
import os


def is_dev_mode() -> bool:
    in_pycharm = False
    try:
        in_pycharm = "PYCHARM_HOSTED" in os.environ
    except Exception as e:
        log.write_exception(exception=e)

    return in_pycharm


def main(api_key_file_path: str,
         file_list: [str],
         out_dir: str,
         country_alpha_2: str,
         language_alpha_2: str,
         output_country: str,
         output_language: str,
         tokens_per_minute: int = -1,
         keep_history: bool = False,
         delay: float = 2.0):
    # checking if api file exists
    if not os.path.exists(path=api_key_file_path) or not os.path.isfile(api_key_file_path):
        raise Exception("API key file not found or invalid at: " + api_key_file_path)

    if is_dev_mode():
        delay = 0.01

    if file_list is None:
        file_list = []

    f = open(api_key_file_path)
    api_key = f.read().strip()
    f.close()

    # updating country codes
    country_alpha_2 = str(country_alpha_2).lower()
    language_alpha_2 = str(language_alpha_2).lower()

    # generating openAI interface
    model = gpt_model_interface.TranslationGPT(
        api_key=api_key,
        output_country=output_country,
        output_language=output_language
    )

    # looping over every subtitle file
    for i in range(len(file_list)):
        subtitle_file: str = file_list[i]
        log.write(f'Translating file: {i + 1}/{len(file_list)}: {os.path.basename(subtitle_file)}')

        subs: subtitles.Subtitles = subtitles.Subtitles(input_file_path=subtitle_file)
        response_times: [int] = []
        eta_text = '?'
        model.clear_session()
        total_token_count: int = 0

        # tokens per minute limits
        current_tpm_tokens: int = 0
        current_tpm_ms: int = 0

        for j in range(len(subs)):
            # updating progressbar
            utils.print_progress_bar(iteration=j + 1,
                                     total=len(subs),
                                     eta_text=eta_text,
                                     tokens_session=model.tokens_generated + model.tokens_generated,
                                     tokens_total=total_token_count)

            # clearing history if requested
            if not keep_history:
                model.clear_session()

            # getting the current line
            line_current: subtitles.Line = subs[j]
            if j >= 4 and is_dev_mode():
                continue

            # prompting model for translation
            translation, gpt_response = model.translate_line(line=line_current.spoken_line,
                                                             silent=True)
            line_current.spoken_line = translation

            # sleeping a number of seconds specified by the user
            time.sleep(delay)

            # collecting tokens
            current_tpm_tokens += gpt_response.total_tokens
            current_tpm_ms += int(gpt_response.response_ms + int(delay * 1000))
            total_token_count += gpt_response.total_tokens

            if current_tpm_ms >= 60000:
                # if more than one minute has passed, reset the minute and token counter
                current_tpm_ms = 0
                current_tpm_tokens = 0
            if tokens_per_minute > 0 and current_tpm_tokens >= tokens_per_minute:
                # if less than one minute has passed and tokens have exceeded maximum:
                #   let's wait a minute and reset counter
                current_tpm_tokens = 0
                current_tpm_ms = 0
                time.sleep(61)

            # updating eta text
            response_times.append(int(gpt_response.response_ms + int(delay * 1000)))
            average_times = int(np.average(response_times))
            eta_text = utils.format_ms(milliseconds=average_times * (len(subs) - j))

        # printing an empty line to flush console
        print('')

        # saving the translated file
        out_file_name = subs.file_name_without_extension()
        out_file_path = f'{out_dir}{os.sep}{out_file_name}.{country_alpha_2}.{language_alpha_2}.srt'

        f = open(out_file_path, 'w')
        f.write(subs.format())
        f.close()

        log.write(f'Saved translation: {out_file_path}')


def extract_input_language(input_language: str):
    if input_language is None:
        raise Exception('Undefined language to translate into.')

    input_language = str(input_language).strip()
    country = None

    if len(input_language) <= 3:
        # is this a iso alpha 2/3 code?
        country = pycountry.countries.get(alpha_3=input_language)
        if country is None:
            country = pycountry.countries.get(alpha_2=input_language)

    if country is None:
        try:
            pycountry.countries.lookup(input_language)
        except LookupError:
            country = None

    if country is None:
        try:
            pycountry.countries.search_fuzzy(input_language)[0]
        except LookupError:
            country = None

    if country is None:
        raise AttributeError(f'Failed to detect language from {input_language}. '
                             f'Try ISO 3166-1: alpha-2 code. Example: "de" for "Germany", "es" for Spain, etc.')

    language = pycountry.languages.get(alpha_3=country.alpha_3)
    return country, language


def extract_input_dirs(input_dirs: str, output_dir: str) -> ([str], str):
    if args.input is None:
        input_dirs = get_absolute_path()

    input_dirs = str(input_dirs).strip()
    if not os.path.exists(path=input_dirs):
        raise Exception(f'Input path does not exist: {input_dirs}')

    if output_dir is None:
        output_dir = input_dirs

    if os.path.isfile(input_dirs):
        return [input_dirs], output_dir

    file_list = []
    for file in os.listdir(input_dirs):
        if file.lower().endswith('.srt'):
            file_list.append(input_dirs + os.sep + file)
    return file_list, output_dir


def get_absolute_path() -> str:
    absolute_path = os.path.abspath(__file__)
    absolute_path = os.path.abspath(os.path.join(absolute_path, os.pardir))
    return absolute_path


# main function where the code enters the game!
if __name__ == '__main__':
    log.write(f'Running AI subtitle translations. Logged in as: "{utils.get_username()}".')

    absolute_path = get_absolute_path()
    log.set_log_dir(new_dir=absolute_path)

    # If not in pycharm, checking the arguments
    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--') + 1:]
    parser = argparse.ArgumentParser(description='Runs the project_lotte scheduling.')

    ######################
    # Required Arguments
    parser.add_argument('-key', '--api_key', type=str, required=True,
                        help='Filepath for a text file that contains your open AI api key. Required.')
    parser.add_argument('-l', '--language', type=str, required=True,
                        help='The language to translate into.'
                             ' Recommended to use two character country code (ISO 3166-1: alpha-2).'
                             ' Example: "de" for "Germany", "es" for Spain, etc.'
                             ' Required.')

    # Optional arguments
    parser.add_argument('-tpm', '--tokens_per_minute', type=int, required=False, default=-1,
                        help='Maximum tokens per minute to use.'
                             ' Typical rate limit reached for gpt-3.5-turbo is 160000.'
                             ' Visit https://platform.openai.com/account/rate-limits to learn more.')
    parser.add_argument('-i', '--input', type=str, required=False,
                        help='Single file or directory to translate. If empty, the current directory is used.')
    parser.add_argument('-o', '--output', type=str, required=False,
                        help='Directory to save the translated files in. If empty, the input directory is used.')
    parser.add_argument('-d', '--delay', type=float, required=False, default=0,
                        help='Delay (in seconds) between every API call. Use to handle rate limit.')
    parser.add_argument('-k', '--keep_history', type=bool, required=False, default=False,
                        help='For every file translated, keeps a session history.'
                             ' Results in more cohesive translations (as the model remembers previous lines spoken).'
                             ' Raises tokens count significantly. Keep cost and rate limits in mind!')

    # Parsing the arguments
    args = parser.parse_args()

    # Extracting the language
    country, language = extract_input_language(args.language)

    # Extracting input dir:
    file_list, out_dir = extract_input_dirs(args.input, args.output)
    country_alpha_2 = country.alpha_2
    language_alpha_2 = language.alpha_2

    # Informing the user via terminal
    log.write(f'Translating {len(file_list)} subtitle(s) into {language.name} ({country.name}).')
    log.write(f'Translations are saved in: {out_dir}')

    # Running the script
    main(api_key_file_path=args.api_key,
         file_list=file_list,
         out_dir=out_dir,
         country_alpha_2=country_alpha_2,
         language_alpha_2=language_alpha_2,
         output_country=country.name,
         tokens_per_minute=args.tokens_per_minute,
         delay=args.delay,
         keep_history=args.keep_history,
         output_language=language.name
         )
    log.write('Finished running "main()".')
