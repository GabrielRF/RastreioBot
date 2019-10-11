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

bot = telebot.TeleBot(TOKEN)
client = MongoClient()
db = client.rastreiobot

def del_code(code):
    cursor = db.rastreiobot.delete_one (
    { "code" : code.upper() }
    )

if __name__ == '__main__':
    code = sys.argv[1]
    del_code(code)
