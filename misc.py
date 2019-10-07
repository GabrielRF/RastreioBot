import re
import apicorreios as correios
import apitrackingmore as trackingmore
from pymongo import MongoClient
from telebot import types


client = MongoClient()
db = client.rastreiobot

def check_type(code):
    s10 = (r"^[A-Za-z]{2}\d{9}[A-Za-z]{2}$")
    ali = (r"^([A-Za-z]{2}\d{14}|[A-Za-z]{4}\d{9}|\d{10}|[A-Za-z]{5}\d{10}[A-Za-z]{2})$")

    if re.search(s10, str(code)):
        return correios
    elif re.search(ali, str(code)):
        return trackingmore
    else:
        return None


def send_clean_msg(bot, id, txt):
    markup_clean = types.ReplyKeyboardRemove(selective=False)
    bot.send_message(id, txt, parse_mode='HTML', reply_markup=markup_clean)


def check_package(code):
    cursor = db.rastreiobot.find_one({"code": code.upper()})
    if cursor:
        return True
    return False
