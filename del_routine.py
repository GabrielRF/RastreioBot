import configparser
import logging.handlers
from datetime import datetime
from time import time

import telebot
from pymongo import MongoClient

config = configparser.ConfigParser()
config.read('bot.conf')

TOKEN = config['RASTREIOBOT']['TOKEN']
int_del = int(config['RASTREIOBOT']['int_del'])
LOG_DEL_FILE = config['RASTREIOBOT']['delete_log']

logger_info = logging.getLogger('InfoLogger')
logger_info.setLevel(logging.DEBUG)
handler_info = logging.handlers.TimedRotatingFileHandler(LOG_DEL_FILE,
    when='midnight', interval=1, backupCount=5, encoding='utf-8')
logger_info.addHandler(handler_info)

bot = telebot.TeleBot(TOKEN)
client = MongoClient()
db = client.rastreiobot


def del_user(code, msg):
    logger_info.info(str(datetime.now()) + '\t' + code + '\t' + msg.replace('\n',' '))
    db.rastreiobot.delete_one (
    { "code" : code.upper() }
    )


if __name__ == '__main__':
    cursor1 = db.rastreiobot.find()
    logger_info.info(str(datetime.now()) + '\t' + '--- DELETE running! ---' )
    for elem in cursor1:
        code = elem['code']
        time_dif = int(time() - float(elem['time']))
        old_state = elem['stat'][len(elem['stat'])-1]
        if 'Entrega Efetuada' in old_state:
            if time_dif > int_del:
                del_user(elem['code'], old_state)
        elif 'Objeto entregue ao destinatário' in old_state:
            if time_dif > int_del:
                del_user(elem['code'], old_state)
        elif 'Objeto apreendido por órgão de fiscalização' in old_state:
            if time_dif > int_del:
                del_user(elem['code'], old_state)
        elif 'Objetvo devolvido' in old_state:
            if time_dif > int_del:
                del_user(elem['code'], old_state)
        elif 'Objetvo roubado' in old_state:
            if time_dif > int_del:
                del_user(elem['code'], old_state)
        elif 'Aguardando recebimento pelo ECT.' in old_state:
            if time_dif > int_del:
                del_user(elem['code'], old_state)
        elif 'Aguardando recebimento pela ECT.' in old_state:
            if time_dif > int_del:
                del_user(elem['code'], old_state)
        elif 'Objeto não localizado no fluxo postal.' in old_state:
            if time_dif > int_del:
                del_user(elem['code'], old_state)
        elif 'Delivered' in old_state:
            if time_dif > int_del:
                del_user(elem['code'], old_state)
        else:
            if time_dif > 2 * int_del:
                del_user(elem['code'], old_state)
