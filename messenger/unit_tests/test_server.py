import unittest
from time import time
from ..common.utils import *

sys.path.append('..')


class TestSocket:
    def __init__(self, test_dict):
        self.test_dict = test_dict

    def send(self, message_to_send):
        json_message = json.dumps(self.test_dict)
        self.encoded_message = json_message.encode(ENCODING)
        self.recieved_message = message_to_send

    def recv(self, max_len):
        json_message = json.dumps(self.test_dict)
        return json_message.encode(ENCODING)


class Tests(unittest.TestCase):
    test_dict = {
        ACTION: PRESENCE,
        TIME: time(),
        USER: {
            ACCOUNT_NAME: 'Guest',
        },
    }
    test_dict_ok = {RESPONSE: 200}
    test_dict_error = {
        RESPONSE: 400,
        ERROR: 'Bad request',
    }

    def test_send_message(self):
        test_socket = TestSocket(self.test_dict)
        send_message(test_socket, self.test_dict)
        self.assertEqual(test_socket.encoded_message, test_socket.recieved_message)
        self.assertRaises(NonDictInpuErrorError, send_message, test_socket, 1111)

    def test_get_message(self):
        test_socket_ok = TestSocket(self.test_dict_ok)
        test_socket_error = TestSocket(self.test_dict_error)
        self.assertEqual(get_message(test_socket_ok), self.test_dict_ok)
        self.assertEqual(get_message(test_socket_error), self.test_dict_error)


if __name__ == "__main__":
    unittest.main()
