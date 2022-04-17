import sys
import unittest
from time import time

from common.errors import ReqFieldMissingError, ServerError
from ..client import create_presence, process_response_answer
from ..common.variables import *

sys.path.append('../')


class TestClass(unittest.TestCase):
    def test_def_presence(self):
        test_presence = create_presence('Guest')
        test_presence[TIME] = time()
        self.assertEqual(test_presence,
                         {
                             ACTION: PRESENCE,
                             TIME: time(),
                             USER: {
                                 ACCOUNT_NAME: 'Guest',
                             },
                         })

    def test_good_answer(self):
        self.assertEqual(process_response_answer(
            {RESPONSE: 200, }), '200 : OK')

    def test_bad_answer(self):
        self.assertRaises(ServerError,
                          process_response_answer,
                          {RESPONSE: 400,
                           ERROR: 'Bad request', })

    def test_no_response(self):
        self.assertRaises(ReqFieldMissingError,
                          process_response_answer,
                          {ERROR: 'No response', })


if __name__ == '__main__':
    unittest.main()
