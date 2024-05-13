import os
import datetime
from base64 import b64decode, b64encode


def convert_to_file_1(downloaded_file):
    data = b64encode(downloaded_file.read()).decode('ascii')
    print(f'data = {data[:100]}')
    time = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    source_file = os.path.join('files', 'audio_files_s2t', time)
    print(f'source_file = {source_file}')
    bytes_data = bytes(data, encoding='ascii')
    b64_data = b64decode(bytes_data)
    with open(source_file, 'wb') as audio_file:
        audio_file.write(b64_data)


def convert_to_file_2(bytesio_obj):
    time = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
    audio_file = os.path.join('files', 'audio_files_s2t', time + '.wav')
    with open(audio_file, "wb") as file:
        file.write(bytesio_obj.getvalue())
    return audio_file
