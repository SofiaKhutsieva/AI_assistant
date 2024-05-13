from base64 import b64decode, b64encode

file_type_2_base64_prefix = {
    'xlsx': 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,',
    'jpg': 'data:image/jpeg;base64,',
    'png': 'data:image/jpeg;base64,',
    'pdf': 'data:application/pdf;base64,',
    'docx': 'data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,',
    'xlsm': 'data:application/vnd.ms-excel.sheet.macroEnabled.12;base64,',
    'xls': 'data:application/vnd.ms-excel;base64,',
    'wav': 'data:application/wav;base64,',
    'ogg': 'data:application/ogg;base64,',
    'mpeg': 'data:audio/mpeg;base64',
}

def convert_file_to_base64(document_path):
    with open(document_path, 'rb') as file :
        encoded = b64encode(file.read()).decode("utf-8")
    encoded = file_type_2_base64_prefix[document_path.split('.')[-1]] + encoded
    return  encoded