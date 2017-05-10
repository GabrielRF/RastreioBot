from check_update import check_update
from datetime import datetime
from pymongo import MongoClient
from time import time, sleep

import configparser
import logging
import logging.handlers
import telebot
import sys

config = configparser.ConfigParser()
config.sections()
config.read('bot.conf')

TOKEN = config['RASTREIOBOT']['TOKEN']
int_del = int(config['RASTREIOBOT']['int_del'])
LOG_INFO_FILE = config['RASTREIOBOT']['routine_log']

logger_info = logging.getLogger('InfoLogger')
logger_info.setLevel(logging.DEBUG)
handler_info = logging.handlers.RotatingFileHandler(LOG_INFO_FILE,
    maxBytes=10240, backupCount=5, encoding='utf-8')
logger_info.addHandler(handler_info)

bot = telebot.TeleBot(TOKEN)
client = MongoClient()
db = client.rastreiobot

def del_user(code):
    cursor = db.rastreiobot.delete_one (
    { "code" : code.upper() }
    )

if __name__ == '__main__':
    cursor1 = db.rastreiobot.find()
    logger_info.info(str(datetime.now()) + '\t' + '--- DELETE running! ---' )
    for elem in cursor1:
        code = elem['code']
        time_dif = int(time() - float(elem['time']))
        old_state = elem['stat'][len(elem['stat'])-1]
        print(str(elem['code']) + ' ' + str(time_dif))
        if 'Entrega Efetuada' in old_state:
            if time_dif > int_del:
                # print(elem['code'])
                del_user(elem['code'])
        if 'Objeto entregue ao destinatário' in old_state:
            if time_dif > int_del:
                # print(elem['code'])
                del_user(elem['code'])
        if 'Objeto apreendido por órgão de fiscalização' in old_state:
            if time_dif > int_del:
                del_user(elem['code'])
        if 'Objetvo devolvido' in old_state:
            if time_dif > int_del:
                del_user(elem['code'])
