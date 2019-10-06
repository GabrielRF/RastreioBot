import re
from pymongo import MongoClient
from telebot import types


client = MongoClient()
db = client.rastreiobot


def send_clean_msg(bot, id, txt):
    markup_clean = types.ReplyKeyboardRemove(selective=False)
    bot.send_message(id, txt, parse_mode='HTML', reply_markup=markup_clean)


def check_package(code):
    cursor = db.rastreiobot.find_one({"code": code.upper()})
    if cursor:
        return True
    return False
