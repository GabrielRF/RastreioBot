import configparser
import logging
import logging.handlers

_config = configparser.ConfigParser()
_config.sections()
_config.read('bot.conf')

LOG_ALERTS_FILE = _config['RASTREIOBOT']['alerts_log']
LOG_ERROR_FILE = _config['RASTREIOBOT']['error_log']
LOG_INFO_FILE = _config['RASTREIOBOT']['text_log']

def get_logger(logger_name):
    logger = logging.getLogger(logger_name)

    # if logger has at least 3 handlers
    # it's already been set previously, so just return it
    if len(logger.handlers) >= 3:
        return logger

    # create handlers
    alerts_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_ALERTS_FILE, when='midnight', interval=1, backupCount=10, encoding='utf-8'
    )
    error_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_ERROR_FILE, when='midnight', interval=1, backupCount=10, encoding='utf-8'
    )
    info_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_INFO_FILE, when='midnight', interval=1, backupCount=10, encoding='utf-8'
    )
    alerts_handler.setLevel(logging.WARNING)
    error_handler.setLevel(logging.ERRO)
    info_handler.setLevel(logging.INFO)

    # create formatters and add them to handlers
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s \t%(message)s')
    alerts_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)
    info_handler.setFormatter(formatter)

    logger.addHandler(info_handler)
    logger.addHandler(alerts_handler)
    logger.addHandler(error_handler)

    return logger

