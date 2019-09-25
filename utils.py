import datetime


# Add to log
def log(logger, chatid, message_id, text):
    logger.info(
        str(datetime.now()) +
        '\t' + str(chatid) + ' \t' +
        str(message_id) + ' \t' + str(text)
    )

