import sys
import logging
import socket

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


def login_required(func):
    def checker(*args, **kwargs):
        from messenger.server.core import MessageProcessor
        from common.variables import ACTION, PRESENCE
        if isinstance(args[0], MessageProcessor):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True

            for arg in args:
                if isinstance(arg, dict):
                    if ACTION in arg and arg[ACTION] == PRESENCE:
                        found = True
            if not found:
                raise TypeError
        return func(*args, **kwargs)

    return checker
