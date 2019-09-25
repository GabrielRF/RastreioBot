from datetime import datetime


# Add to log
def log(logger, text):
    logger.info("{} {}".format(datetime.now(), text))

