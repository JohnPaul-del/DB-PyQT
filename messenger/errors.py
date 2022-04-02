class IncorrectDataRecievedError(Exception):
    def __str__(self):
        return 'Incorrect data received error'


class NonDictInpuErrorError(Exception):
    def __str__(self):
        return 'Non-dictionary inpu error'


class ServerError(Exception):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


class ReqFieldMissingError(Exception):
    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'Field missing: {self.missing_field}'