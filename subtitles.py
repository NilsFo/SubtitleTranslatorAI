import os

from util import log

compatible_file_formats = ['srt']


class Subtitles:

    def __init__(self, input_file_path: str) -> None:
        super().__init__()

        assert input_file_path is not None
        input_file_path = str(input_file_path)

        if not os.path.exists(path=input_file_path) or not os.path.isfile(input_file_path):
            raise Exception("Subtitle key file not found or invalid at: " + input_file_path)
        if not input_file_path.lower().endswith('.srt'):
            raise Exception("Invalid subtitle file format (sty expected!): " + input_file_path)

        # setting up variables
        self.file_name = os.path.basename(input_file_path)
        self._iter_progress: int = 0

        # reading line by line
        lines_raw = None
        with open(input_file_path) as f:
            lines_raw = [line.rstrip() for line in f]

        self.lines = []
        line_counter = 2

        buffer_speaking_line = ''
        buffer_start_time = ''
        buffer_end_time = ''

        log.write(f'Parsing {self.file_name}', print_to_console=False)
        for i in range(len(lines_raw)):
            current_line = lines_raw[i]
            current_line = str(current_line).strip()
            separator_line_found = False

            if current_line == str(line_counter):
                # separator line found
                separator_line_found = True
                line_counter = line_counter + 1

            elif '-->' in current_line:
                # timestamp line found
                buffer_start_time, buffer_end_time = current_line.strip().split(' --> ')
                buffer_speaking_line = ''

            else:
                # default speaking line found
                buffer_speaking_line = buffer_speaking_line + '\n' + current_line
                buffer_speaking_line = buffer_speaking_line.strip()

            # committing line
            if separator_line_found:
                self.lines.append(Line(
                    index=line_counter - 2,
                    start_time=buffer_start_time,
                    end_time=buffer_end_time,
                    spoken_line=buffer_speaking_line.strip()
                ))

        log.write(f'Finished parsing {len(self.lines)} lines.', print_to_console=False)

    def file_name_without_extension(self):
        return self.file_name[:-4]

    def count(self):
        return len(self.lines)

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, item):
        return self.lines[item]

    def __iter__(self):
        return self

    def __next__(self):
        progress = self._iter_progress
        self._iter_progress = progress + 1

        if progress == self.count():
            self._iter_progress = 0
            raise StopIteration()

        return self.lines[progress]

    def format(self) -> str:
        formatted_text = ''

        for i in range(len(self)):
            line: Line = self[i]

            formatted_text = formatted_text + str(line.index) + '\n'
            formatted_text = formatted_text + f'{line.start_time} --> {line.end_time}' + '\n'
            formatted_text = formatted_text + line.spoken_line + '\n\n'

        return formatted_text


class Line:
    def __init__(self, index: int, start_time: str, end_time: str, spoken_line: str) -> None:
        super().__init__()
        assert index is not None and start_time is not None and end_time is not None and spoken_line is not None

        self.index: int = int(index)
        self.start_time: str = str(start_time).strip()
        self.end_time: str = str(end_time).strip()
        self.spoken_line: str = str(spoken_line).strip()

    def __str__(self):
        short_line = self.spoken_line.replace('\n', ' ').replace('  ', ' ').strip()
        return f'Subtitle line #{self.index}: "{short_line}": {self.start_time} -> {self.end_time}'


if __name__ == '__main__':
    print('Cannot run this file.')

    s = Subtitles(
        input_file_path='input/Scavengers.Reign.S01E01.The.Signal.1080p.WEBRip.AAC.5.1.x265.10bit.RED_en.en.srt')
