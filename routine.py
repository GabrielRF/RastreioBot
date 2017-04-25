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
int_check = int(config['RASTREIOBOT']['int_check'])
LOG_INFO_FILE = config['RASTREIOBOT']['routine_log']
PATREON = config['RASTREIOBOT']['patreon']

logger_info = logging.getLogger('InfoLogger')
logger_info.setLevel(logging.DEBUG)
handler_info = logging.handlers.TimedRotatingFileHandler(LOG_INFO_FILE,
    when='midnight', interval=1, backupCount=5, encoding='utf-8')
logger_info.addHandler(handler_info)

bot = telebot.TeleBot(TOKEN)
client = MongoClient()
db = client.rastreiobot

multiple = sys.argv[1]

def get_package(code):
    stat = check_update(code)
    # print(stat)
    if stat == 0:
        stat = 'Sistema dos Correios fora do ar.'
    elif stat == 1:
        stat = None
    else:
        cursor = db.rastreiobot.update_one (
        { "code" : code.upper() },
        {
            "$set": {
                "stat" : stat,
                "time" : str(time())
            }
        })
        stat = 10
    return stat

if __name__ == '__main__':
    sleep(60*int(multiple))
    cursor1 = db.rastreiobot.find()
    start = time()
    sent = 0
    for elem in cursor1:
        # print(elem['code'] + ' ' + elem['code'][10])
        if elem['code'][10] != multiple:
            continue
        print(elem['code'] + '\t' + elem['time'])
        now = time()
        if int(now) - int(start) > 599:
            logger_info.info(str(datetime.now()) + '\tRoutine too long. ' + str(multiple))
            break
        code = elem['code']
        time_dif = int(time() - float(elem['time']))
        for user in elem['users']:
            if user not in PATREON:
                if time_dif < int_check:
                    continue
            else:
                print(user)
        old_state = elem['stat'][len(elem['stat'])-1]
        len_old_state = len(elem['stat'])
        if 'objeto entregue ao' in old_state.lower():
            continue
        get_package(code)
        cursor2 = db.rastreiobot.find_one(
        {
            "code": code
        })
        len_new_state = len(cursor2['stat'])
        if len_old_state != len_new_state:
            for user in elem['users']:
                logger_info.info(str(datetime.now()) + '\tUPDATE: '
                    + str(code) + ' \t' + str(user) + '\t' + str(sent))
                try:
                    message = (str(u'\U0001F4EE') + '<b>' + code + '</b>\n')
                    if elem[user] != code:
                        message = message + elem[user] + '\n'
                    message = (
                        message + '\n'
                        +  cursor2['stat'][len(cursor2['stat'])-1])
                    if 'Objeto entregue ao de' in message.lower():
                        message = (message + '\n\n'
                        + str(u'\U00002B50')
                        + '<a href="https://telegram.me/storebot?start=rastreiobot">'
                        + 'Avalie o bot</a> - '
                        + str(u'\U0001F4B5')
                        + '<a href="http://grf.xyz/paypal">Colabore</a>')
                    bot.send_message(user, message, parse_mode='HTML',
                        disable_web_page_preview=True)
                    sent = sent + 1
                except Exception as e:
                    logger_info.info(str(datetime.now())
                         + '\tEXCEPT: ' + str(user) + ' '
                         + code + '\t -> ' + str(e))
                    pass
        sleep(0.03)
    # logger_info.info(str(datetime.now()) + '\t' + '--- UPDATE ' + multiple + ' finished! --- ' + '\tAlertas: ' + str(sent))
