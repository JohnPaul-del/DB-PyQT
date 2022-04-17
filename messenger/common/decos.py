import sys
import logging

import messenger.logs.client_log_cnf
import messenger.logs.server_log_cnf

if sys.argv[0].find('client') == -1:
    logger = logging.getLogger('server')
else:
    logger = logging.getLogger('client')


def log(write_to_log):
    def save_log(*args, **kwargs):
        logger.debug(f'Func: {write_to_log.__name__} | Params: {args}, {kwargs} | Module: {write_to_log.__module__}')
        result = write_to_log(*args, **kwargs)
        return result
    return save_log
