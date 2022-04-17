import json
import sys

sys.path.append("..")

from messenger.common.variables import *
from errors import IncorrectDataRecievedError, NonDictInpuErrorError
from decos import log


@log
def get_message(client):
    encode_response = client.recv(MAX_PACKAGE_LENGTH)
    if isinstance(encode_response, bytes):
        json_response = encode_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        else:
            raise IncorrectDataRecievedError
    else:
        raise IncorrectDataRecievedError


@log
def send_message(sock, message):
    if not isinstance(message, dict):
        raise NonDictInpuErrorError
    json_message = json.dumps(message)
    encode_message = json_message.encode(ENCODING)
    sock.send(encode_message)
