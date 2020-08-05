import configparser
import logging.handlers
import sys
from datetime import datetime
from time import time, sleep
from utils.misc import check_update

from rastreio import db
import requests
import sentry_sdk
import telebot
from pymongo import MongoClient

config = configparser.ConfigParser()
config.read('bot.conf')

TOKEN = config['RASTREIOBOT']['TOKEN']
int_check = int(config['RASTREIOBOT']['int_check'])
LOG_ALERTS_FILE = config['RASTREIOBOT']['alerts_log']
PATREON = config['RASTREIOBOT']['patreon']
BANNED = config['RASTREIOBOT']['banned']
INTERVAL = 0.03

bot = telebot.TeleBot(TOKEN)

multiple = sys.argv[1]
print(multiple)
def get_package(code):
    stat = check_update(code)
    print(stat)
    if stat == 0:
        stat = 'Sistema dos Correios fora do ar.'
    elif stat == 1:
        stat = None
    elif stat == 3:
        stat = None
    else:
        db.update_package(code, stat=stat, time=str(time()))
        stat = 10
    return stat

def check_system():
    try:
        URL = ('http://webservice.correios.com.br/')
        response = requests.get(URL, timeout=3)
    except:
        logger_info.info(str(datetime.now()) + '\tCorreios indisponível')
        return False
    if '200' in str(response):
        return True
    else:
        logger_info.info(str(datetime.now()) + '\tCorreios indisponível')
        return False

if __name__ == '__main__':
    #sleep(60*int(multiple))
    logger_info = logging.getLogger('InfoLogger')
    handler_info = logging.FileHandler(LOG_ALERTS_FILE)
    logger_info.setLevel(logging.DEBUG)
    logger_info.addHandler(handler_info)

    sentry_url = config['SENTRY']['url']
    if sentry_url:
        sentry_sdk.init(sentry_url)

    cursor1 = db.all_packages()
    start = time()
    sent = 1
    if check_system():
        pass
    else:
        sys.exit()
    for elem in cursor1:
        try:
            if elem['code'][5] != multiple:
                continue
            now = time()
            timediff = int(now) - int(start)
            #if timediff > 800:
            #    logger_info.info(str(datetime.now()) + '\t' + multiple + '\tRoutine too long')
            #    break
            code = elem['code']
            time_dif = int(time() - float(elem['time']))
            for user in elem['users']:
                if user not in PATREON:
                    if time_dif < int_check:
                        continue
                else:
                    print(user)
            try:
                old_state = elem['stat'][len(elem['stat'])-1]
                len_old_state = len(elem['stat'])
            except:
                len_old_state = 1
            if 'objeto entregue ao' in old_state.lower():
                continue
            elif 'objeto apreendido por órgão de fiscalização' in old_state.lower():
                continue
            elif 'objeto devolvido' in old_state.lower():
                continue
            elif 'objeto roubado' in old_state.lower():
                continue
            elif 'delivered' in old_state.lower():
                continue
            try:
                stat = get_package(code)
            except:
                sleep(3000)
                stat = get_package(code)
            if stat == 0:
                break
            cursor2 = db.search_package(code)
            try:
                len_new_state = len(cursor2['stat'])
            except:
                len_new_state = 1
            if len_old_state != len_new_state:
                len_diff = len_new_state - len_old_state
                for user in elem['users']:
                    logger_info.info(str(datetime.now()) + ' ' + multiple + ' '
                        + str(code) + ' \t' + str(user) + ' \t' + str(sent) + '\t'
                        + str(timediff) + '\t' + str(len_old_state) + '\t'
                        + str(len_new_state) + '\t' + str(len_diff))
                    try:
                        try:
                            message = (str(u'\U0001F4EE') + '<b>' + code + '</b> (' + elem['code_br']  +  ')\n')
                        except:
                            message = (str(u'\U0001F4EE') + '<b>' + code + '</b>\n')
                        try:
                            if code not in elem[user]:
                                message = message + elem[user] + '\n'
                        except:
                            pass
                        for k in reversed(range(1,len_diff+1)):
                            message = (
                                message + '\n'
                                + cursor2['stat'][len(cursor2['stat'])-k] + '\n')
                        if 'objeto entregue' in message.lower() and user not in PATREON:
                            message = (message + '\n'
                            + str(u'\U0001F4B3')
                            + ' <a href="http://grf.xyz/assine">Assine o bot</a> - '
                            + str(u'\U0001F4B5')
                            + ' <a href="http://grf.xyz/picpay">Colabore</a>')
                        if len_old_state < len_new_state:
                            if user not in BANNED:
                                bot.send_message(str(user), message, parse_mode='HTML',
                                    disable_web_page_preview=True)
                            sent = sent + 1
                    except Exception as e:
                        logger_info.info(str(datetime.now())
                             + '\tEXCEPT: ' + str(user) + ' ' + code + ' ' + str(e))
                        continue
        except Exception as e:
            logger_info.info(str(datetime.now()) + ' ' + multiple + ' EXCEPT: ' + str(e)
                + '\t' + str(code) + ' \t' + str(user))
            sys.exit()
