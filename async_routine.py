import configparser
import logging.handlers
import sys
from datetime import datetime
from time import time, sleep
from misc import check_update
from misc import async_check_update

import requests
import telebot

import asyncio
import motor.motor_asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils import executor


config = configparser.ConfigParser()
config.read('bot.conf')


TOKEN = config['RASTREIOBOT']['TOKEN']
int_check = int(config['RASTREIOBOT']['int_check'])
LOG_ALERTS_FILE = config['RASTREIOBOT']['alerts_log']
PATREON = config['RASTREIOBOT']['patreon']
INTERVAL = 0.03

logger_info = logging.getLogger('InfoLogger')
handler_info = logging.FileHandler(LOG_ALERTS_FILE)
logger_info.setLevel(logging.DEBUG)
logger_info.addHandler(handler_info)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
client = motor.motor_asyncio.AsyncIOMotorClient()
db = client.rastreiobot

async def get_package(code):
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
        response = requests.get(URL, timeout=3)
    except:
        logger_info.info(str(datetime.now()) + '\tCorreios indisponível')
        return False
    if '200' in str(response):
        return True
    else:
        logger_info.info(str(datetime.now()) + '\tCorreios indisponível')
        return False


async def up_package(elem):
    code = elem['code']

    try:
        old_state = elem['stat'][len(elem['stat'])-1]
        len_old_state = len(elem['stat'])
    except:
        old_state = ""
        len_old_state = 1
    if 'objeto entregue ao' in old_state.lower():
        return
    elif 'objeto apreendido por órgão de fiscalização' in old_state.lower():
        return
    elif 'objeto devolvido' in old_state.lower():
        return
    elif 'objeto roubado' in old_state.lower():
        return
    elif 'delivered' in old_state.lower():
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
                await bot.send_message(str(user), message, parse_mode='HTML',
                    disable_web_page_preview=True)
        except Exception as e:
            logger_info.info(str(datetime.now())
                    + ' EXCEPT: ' + str(user) + ' ' + code + ' ' + str(e))
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
        n += 1
        tasks.append(up_package(elem))
        if n > 10000:
            break

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    executor.start(dp, async_main())



# ida ao banco
# chamada da api
# fala com o usuario
