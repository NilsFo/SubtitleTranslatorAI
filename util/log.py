import os
from pathlib import Path
from typing import Union

# from util import file_manager
from util.utils import format_exception
from util.utils import gct

log_dir_base: str = ''


def set_log_dir(new_dir: str):
    if not os.path.exists(path=new_dir) or not os.path.isdir(new_dir):
        raise Exception("Log directory not found or invalid at: " + new_dir)

    global log_dir_base
    log_dir_base = new_dir + os.sep


def write_exception(exception: Exception,
                    include_timestamp: bool = True,
                    print_to_console_message: bool = True,
                    include_in_files_message: bool = True,
                    print_to_console_stack_trace: bool = None,
                    include_in_files_stack_trace: bool = None
                    ):
    assert print_to_console_message is not None
    assert include_in_files_message is not None
    if print_to_console_stack_trace is None:
        print_to_console_stack_trace = print_to_console_message
    if include_in_files_stack_trace is None:
        include_in_files_stack_trace = include_in_files_message

    description, stacktrace_lines = format_exception(exception)

    write(output=description,
          include_in_static_log=True,
          print_to_console=print_to_console_message,
          include_timestamp=include_timestamp,
          include_in_files=include_in_files_message)
    for i in range(len(stacktrace_lines)):
        line = '\t' + str(stacktrace_lines[i])
        write(output=line,
              include_in_static_log=True,
              print_to_console=print_to_console_stack_trace,
              include_timestamp=False,
              include_in_files=include_in_files_stack_trace)


def write(output: Union[str, list],
          include_in_static_log=False,
          print_to_console: bool = True,
          include_timestamp: bool = True,
          include_in_files: bool = True):
    if output is None:
        output = '<none>'

    if type(output) == list:
        for o in output:
            write(output=o,
                  include_in_static_log=include_in_static_log,
                  print_to_console=print_to_console,
                  include_timestamp=include_timestamp,
                  include_in_files=include_in_files)
        return

    try:
        output = str(output)
        _write(output=output, print_to_console=print_to_console, include_timestamp=include_timestamp,
               include_in_files=include_in_files, include_in_static_log=include_in_static_log)
    except Exception as e:
        print('Failed to log: "' + str(output).strip() + '"!')
        print(str(e))

        description, stacktrace_lines = format_exception(e)
        print(e)
        for line in stacktrace_lines:
            print(line)


def _write(output,
           include_in_static_log: bool = False,
           print_to_console: bool = True,
           include_timestamp: bool = True,
           include_in_files: bool = True):
    output = str(output)
    log_files = get_log_files()

    if include_timestamp:
        timestamp = gct()
        output = '[' + timestamp + '] ' + output

    if print_to_console:
        print(output)

    if include_in_files:
        for current_out_file in log_files:
            try:
                if os.path.exists(current_out_file):
                    f = open(current_out_file, 'a')
                    f.write('\n')
                else:
                    # Creating the parent path
                    parent_path = Path(current_out_file)
                    parent_path = parent_path.parent.absolute()
                    os.makedirs(parent_path, exist_ok=True)
                    f = open(current_out_file, 'w', encoding="utf-8")

                f.write(output)
                f.close()
            except Exception as e:
                print('Failed to log to: ' + str(current_out_file))
                print(str(e))
                # TODO: Better log error


def get_log_files() -> [str]:
    log_files = []

    log_dir = log_dir_base + 'log' + os.sep
    log_file = log_dir + 'log.txt'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    if not os.path.exists(log_file):
        f = open(log_file, 'w')
        f.close()

    log_files.append(log_file)
    return log_files


# def write_model_prompt_history(model, indent: int = 2):
#     file_path = file_manager.output_path_today() + os.sep + 'prompt_history.json'
#     f = open(file_path, 'w', encoding="utf-8")
#     f.write(model.prompt_history_json(indent=indent))
#     f.close()
#     del f


def diagnose():
    # Diagnosing log files
    log_files = get_log_files()
    write('Diagnosing log files.')
    write('Number of log files: ' + str(len(log_files)))
    for file in log_files:
        write('Logging to: ' + str(file))


def main():
    write('Testing the "log" functions.')
    write('This is a test log.')
    diagnose()


if __name__ == "__main__":
    absolute_path = os.path.abspath(__file__)
    absolute_path = os.path.abspath(os.path.join(absolute_path, os.pardir))
    set_log_dir(absolute_path)

    lf = get_log_files()

    print('Checking log files.')
    print('Log count: ' + str(len(lf)))
    for s in lf:
        print(s)

    print('Logging to these files now:')
    write('Test log.', include_in_static_log=True)
