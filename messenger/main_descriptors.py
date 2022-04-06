import logging

logger = logging.getLogger('server')


class Port:
    def __init__(self, instance, value):
        if not 1023 < value < 65536:
            logger.critical(f'Invalid port value: {value}.'
                            f'must be between 1023 and 65535')
            exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
