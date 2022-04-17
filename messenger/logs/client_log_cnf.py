import os
import sys

sys.path.append('..')

import logging
from messenger.common.variables import LOGGING_LEVEL

client_format = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

path = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(path, 'client.log')

steam = logging.StreamHandler(sys.stderr)
steam.setFormatter(client_format)
steam.setLevel(logging.ERROR)

log_file = logging.FileHandler(path, encoding='utf8')
log_file.setFormatter(client_format)

logger = logging.getLogger('client')
logger.addHandler(steam)
logger.addHandler(log_file)
logger.setLevel(LOGGING_LEVEL)

if __name__ == '__main__':
    logger.critical('Fatal ERROR!')
    logger.error('Error!')
    logger.debug('Debug info')
    logger.info('Information')
