import configparser
import logging.handlers
import sys
from datetime import datetime
from time import time, sleep
from utils.misc import check_update
from utils.misc import async_check_update
from utils.misc import check_type
import apis.apicorreios as correios
import apis.apitrackingmore as trackingmore
from rastreio import db as db_ops

import random
import requests
import telebot

import asyncio
import motor.motor_asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils import executor


config = configparser.ConfigParser()
config.read('bot.conf')


TOKEN = config['RASTREIOBOT']['TOKEN']
LOG_ALERTS_FILE = config['RASTREIOBOT']['alerts_log']
PATREON = config['RASTREIOBOT']['patreon']
INTERVAL = 0.03

logger_info = logging.getLogger('InfoLogger')
handler_info = logging.handlers.TimedRotatingFileHandler(
    LOG_ALERTS_FILE, when='midnight', interval=1, backupCount=7, encoding='utf-8'
)
#handler_info = logging.FileHandler(LOG_ALERTS_FILE)
logger_info.setLevel(logging.DEBUG)
logger_info.addHandler(handler_info)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
client = motor.motor_asyncio.AsyncIOMotorClient()
db = client.rastreiobot

async def get_package(code):
    print(code)
    stat = await async_check_update(code)
    if stat == 0:
        stat = 'Sistema dos Correios fora do ar.'
    elif stat == 1:
        stat = None
    elif stat == 3:
        stat = None
    else:
        cursor = await db.rastreiobot.update_one (
        { "code" : code.upper() },
        {
            "$set": {
                "stat" : stat,
                "time" : str(time())
            }
        })
        stat = 10
    return stat


def check_system():
    try:
        URL = ('http://webservice.correios.com.br/')
        response = requests.get(URL, timeout=10)
    except:
        logger_info.info(str(datetime.now()) + '\tCorreios indisponível')
        return False
    if '200' in str(response):
        return True
    else:
        logger_info.info(str(datetime.now()) + '\tCorreios indisponível')
        return False


def is_finished_package(old_state):
    old_state = old_state.lower()
    finished_states = [
        'objeto entregue ao',
        'objeto apreendido por órgão de fiscalização',
        'objeto devolvido',
        'objeto roubado',
        'delivered',
        'postado',
        'ect',
    ]

    for state in finished_states:
        if state in old_state:
            return True

    return False


async def up_package(elem):
    code = elem['code']
    should_retry_finished_package = random.randint(0,5)

    try:
        old_state = elem['stat'][len(elem['stat'])-1].lower()
        len_old_state = len(elem['stat'])
    except:
        old_state = ""
        len_old_state = 1

    if is_finished_package(old_state) and not should_retry_finished_package:
        return

    stat = await get_package(code)
    if stat == 0:
        return

    cursor2 = await db.rastreiobot.find_one(
    {
        "code": code
    })

    try:
        len_new_state = len(cursor2['stat'])
    except:
        len_new_state = 1
    if len_old_state == len_new_state:
        return

    len_diff = len_new_state - len_old_state

    for user in elem.get('users', []):
        logger_info.info(str(datetime.now()) + ' '
            + str(code) + ' \t' + str(user) + ' \t'
            + str(len_old_state) + '\t'
            + str(len_new_state) + '\t' + str(len_diff))
        try:
            try:
                #pacote chines com codigo br
                message = (str(u'\U0001F4EE') + '<b>' + code + '</b> (' + elem['code_br']  +  ')\n')
            except:
                message = (str(u'\U0001F4EE') + '<a href="https://t.me/rastreiobot?start=' + code + '">' + code + '</a>\n')
            try:
                if code not in elem[user]:
                    message = message + '<b>' + elem[user] + '</b>\n'
            except:
                pass

            for k in reversed(range(1,len_diff+1)):
                message = (
                    message + '\n'
                    + cursor2['stat'][len(cursor2['stat'])-k] + '\n')
            if 'objeto entregue' in message.lower() and user not in PATREON:
                message = (message + '\n'
                + str(u'\U0001F4B3')
                + ' Me ajude a manter o projeto vivo!\nEnvie /doar e veja as opções '
                + str(u'\U0001F4B5'))
            if len_old_state < len_new_state:
                await bot.send_message(str(user), message, parse_mode='HTML',
                    disable_web_page_preview=True)
        except Exception as e:
            logger_info.info(str(datetime.now())
                    + ' EXCEPT: ' + str(user) + ' ' + code + ' ' + str(e))
            if 'deactivated' in str(e):
                db_ops.remove_user_from_package(code, str(user))
            elif 'blocked' in str(e):
                db_ops.remove_user_from_package(code, str(user))
            elif 'kicked' in str(e):
                db_ops.remove_user_from_package(code, str(user))
            continue

async def async_main():
    cursor1 = db.rastreiobot.find()
    start = time()
    if check_system():
        pass
    else:
        print("exit")
        return

    # await bot.send_message(str(-340600919), "oi", parse_mode='HTML',
    #                 disable_web_page_preview=True)
    tasks = []
    n = 0
    async for elem in cursor1:
        api_type = check_type(elem['code'])
        if api_type is correios:
            n += 1
            tasks.append(up_package(elem))

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    executor.start(dp, async_main())



# ida ao banco
# chamada da api
# fala com o usuario
