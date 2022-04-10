import sys
import os

sys.path.append('..')
import logging.handlers
from messenger.common.variables import LOGGING_LEVEL

server_format = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

path = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(path, 'server.log')

steam = logging.StreamHandler(sys.stderr)
steam.setFormatter(server_format)
steam.setLevel(logging.DEBUG)
log_file = logging.handlers.TimedRotatingFileHandler(
    path,
    encoding='utf8',
    interval=1,
    when='D',
)
log_file.setFormatter(server_format)

logger = logging.getLogger('server')
logger.addHandler(steam)
logger.addHandler(log_file)
logger.setLevel(LOGGING_LEVEL)

if __name__ == '__main__':
    logger.critical('Fatal Error!')
    logger.error('Error!')
    logger.debug('Debug')
    logger.info('Info')
