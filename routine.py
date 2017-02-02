from check_update import check_update
from pymongo import MongoClient
from time import time, sleep
import configparser
import telebot
import sys

config = configparser.ConfigParser()
config.sections()
config.read('bot.conf')

TOKEN = config['RASTREIOBOT']['TOKEN']
bot = telebot.TeleBot(TOKEN)

client = MongoClient()
db = client.rastreiobot

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
    while True:
        cursor1 = db.rastreiobot.find()
        for elem in cursor1:
            code = elem['code']
            print(code)
            old_state = elem['stat'][len(elem['stat'])-1]
            len_old_state = len(elem['stat'])
            if 'Entrega Efetuada' in old_state:
                continue
            # print(code)
            # print('--------Old: ' + str(len_old_state))
            get_package(code)
            cursor2 = db.rastreiobot.find_one(
            {
                "code": code
            })
            len_new_state = len(cursor2['stat'])
            if len_old_state != len_new_state:
                # print(str(len_old_state) + ' x ' + str(len_new_state))
                for user in elem['users']:
                    print(user)
                    print(elem[user])
                    print(cursor2['stat'][len(cursor2['stat'])-1])
                    try:
                        bot.send_message(user,
                            str(u'\U0001F4EE') + '<b>' + code + '</b>\n'
                            + elem[user] + '\n\n'
                            +  cursor2['stat'][len(cursor2['stat'])-1]
                        , parse_mode='HTML')
                    except:
                        pass
            sleep(1)
        # print('---')
        sleep(1800)
