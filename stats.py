from bs4 import BeautifulSoup
from check_update import check_update
from datetime import datetime
from time import time
from pymongo import MongoClient
from telebot import types

import configparser
import logging
import logging.handlers
import requests
import sys
import telebot

config = configparser.ConfigParser()
config.sections()
config.read('bot.conf')

TOKEN = config['RASTREIOBOT']['TOKEN']
int_check = int(config['RASTREIOBOT']['int_check'])
LOG_INFO_FILE = config['RASTREIOBOT']['log_file']

logger_info = logging.getLogger('InfoLogger')
logger_info.setLevel(logging.DEBUG)
handler_info = logging.handlers.RotatingFileHandler(LOG_INFO_FILE,
    maxBytes=10240, backupCount=5, encoding='utf-8')
logger_info.addHandler(handler_info)

bot = telebot.TeleBot(TOKEN)
client = MongoClient()
db = client.rastreiobot

cursor = db.rastreiobot.find()
not_finished = 0
finished = 0
users = []
for elem in cursor:
    if 'Entrega Efetuada' not in elem['stat'][len(elem['stat'])-1]:
        # print(elem['code'] + ' ' + str(elem['users']))
        not_finished = not_finished + 1
    else:
        finished = finished + 1
    for user in elem['users']:
        if user not in users:
            users.append(user)

print('Em andamento: ' + str(not_finished))
print('Finalizados: ' + str(finished))
print('Usuários: ' + str(len(users)))
