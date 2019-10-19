import configparser
import sys

import telebot
from pymongo import MongoClient

config = configparser.ConfigParser()
config.sections()
config.read('bot.conf')

TOKEN = config['RASTREIOBOT']['TOKEN']
int_del = int(config['RASTREIOBOT']['int_del'])

bot = telebot.TeleBot(TOKEN)
client = MongoClient()
db = client.rastreiobot

def del_code(code):
    db.rastreiobot.delete_one (
    { "code" : code.upper() }
    )

if __name__ == '__main__':
    code = sys.argv[1]
    del_code(code)
