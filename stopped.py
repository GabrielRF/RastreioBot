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
config.read("bot.conf")

TOKEN = config["RASTREIOBOT"]["TOKEN"]
int_check = int(config["RASTREIOBOT"]["int_check"])
LOG_INFO_FILE = config["RASTREIOBOT"]["text_log"]

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.forward_message("9083329", message.from_user.id, message.message_id)
    try:
        bot.send_chat_action(message.chat.id, "typing")
        bot.reply_to(
            message,
            "O bot está passando por uma rápida manutenção. Em breve tudo estará no ar novamente.",
        )
    except:
        pass


bot.polling()
