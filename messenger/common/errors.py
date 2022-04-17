class IncorrectDataRecievedError(Exception):
    """
    Class error - Incorrect received data
    """

    def __str__(self):
        return 'Incorrect data received error'


class NonDictInpuErrorError(Exception):
    """
    Class error - Error dictionary
    """

    def __str__(self):
        return 'Non-dictionary input error'


class ServerError(Exception):
    """
    Class Server Error - Some server error
    """

    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


class ReqFieldMissingError(Exception):
    """
    Class File error - File field missing
    """

    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'Field missing: {self.missing_field}'
