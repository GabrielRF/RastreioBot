from datetime import datetime
from time import time, sleep

import configparser
import logging
import logging.handlers

config = configparser.ConfigParser()
config.sections()
config.read('bot.conf')

LOG_ALERTS_FILE = config['RASTREIOBOT']['alerts_log']

logger_info = logging.getLogger('InfoLogger')
logger_info.setLevel(logging.DEBUG)
handler_info = logging.handlers.TimedRotatingFileHandler(LOG_ALERTS_FILE,
    when='midnight', interval=1, backupCount=5, encoding='utf-8')
logger_info.addHandler(handler_info)

logger_info.info(str(datetime.now()) + ' --- Log rotate ---')
