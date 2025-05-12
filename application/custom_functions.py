import base64


def decode_dash_upload(file_string):
    """decodes string content from dash upload. returns a list of string, each index represents each line in the .txt"""
    decoded = base64.b64decode(file_string)
    file_text = decoded.decode('utf-8')
    file_text = file_text.replace('\r\n', '\n')
    file_text = file_text.split('\n')

    return file_text
