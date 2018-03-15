import logging
import logging.handlers
import random
from datetime import datetime, timedelta
from time import time

import configparser
import msgs
import requests
import telebot
from check_update import check_update
from misc import check_type, send_clean_msg
from pymongo import ASCENDING, MongoClient
from telebot import types

config = configparser.ConfigParser()
config.sections()
config.read('bot.conf')

TOKEN = config['RASTREIOBOT']['TOKEN']
int_check = int(config['RASTREIOBOT']['int_check'])
LOG_INFO_FILE = config['RASTREIOBOT']['text_log']
LOG_ROUTINE_FILE = config['RASTREIOBOT']['routine_log']
LOG_ALERTS_FILE = config['RASTREIOBOT']['alerts_log']
PATREON = config['RASTREIOBOT']['patreon']

logger_info = logging.getLogger('InfoLogger')
logger_info.setLevel(logging.DEBUG)
handler_info = logging.handlers.TimedRotatingFileHandler(
    LOG_INFO_FILE, when='midnight', interval=1, backupCount=7, encoding='utf-8'
)
logger_info.addHandler(handler_info)

bot = telebot.TeleBot(TOKEN)
client = MongoClient()
db = client.rastreiobot

markup_btn = types.ReplyKeyboardMarkup(resize_keyboard=True)
markup_btn.row('/Pacotes', '/Info', '/Concluidos')
markup_clean = types.ReplyKeyboardRemove(selective=False)


# Check if package exists in DB
def check_package(code):
    cursor = db.rastreiobot.find_one({"code": code.upper()})
    if cursor:
        return True
    return False


# Count packages
def count_packages():
    cursor = db.rastreiobot.find()
    print(str(cursor))
    qtd = 0
    wait = 0
    for elem in cursor:
        if 'Aguardando recebimento pel' in str(elem):
            wait = wait + 1
        else:
            qtd = qtd + 1
    return qtd, wait


# List packages of a user
def list_packages(chatid, done):
    aux = ''
    try:
        cursor = db.rastreiobot.find(
            {'users': str(chatid)}).sort(str(chatid), ASCENDING)
        qtd = 0
        for elem in cursor:
            if str(chatid) in elem['users']:
                try:
                    len(elem['stat'])
                except Exception:
                    elem['stat'] = ['Sistema fora do ar']
                if not done:
                    if (
                            'objeto entregue ao' not in status_elem(elem) and
                            'objeto apreendido' not in status_elem(elem) and
                            'objeto roubado' not in status_elem(elem) and
                            'objeto devolvido' not in status_elem(elem)):
                        aux = aux + '/' + elem['code']
                        try:
                            if elem[str(chatid)] != elem['code']:
                                aux = aux + ' ' + elem[str(chatid)]
                        except Exception:
                            pass
                        aux = aux + '\n'
                        qtd = qtd + 1
                else:
                    if (
                            'objeto entregue ao' in status_elem(elem) or
                            'objeto apreendido' in status_elem(elem) or
                            'objeto roubado' in status_elem(elem) or
                            'objeto devolvido' in status_elem(elem)):
                        aux = aux + elem['code']
                        try:
                            if elem[str(chatid)] != elem['code']:
                                aux = aux + ' ' + elem[str(chatid)]
                        except Exception:
                            pass
                        aux = aux + '\n'
                        qtd = qtd + 1
    except Exception:
        bot.send_message('9083329', 'Erro MongoBD')
        qtd = -1
    return aux, qtd


# helper for check text in element
def status_elem(elem):
    return elem['stat'][len(elem['stat']) - 1].lower()


# Get last state of a package from DB
def status_package(code):
    cursor = db.rastreiobot.find_one({
        "code": code
    })
    return cursor['stat']


# Check if user exists on a specific tracking code
def check_user(code, user):
    cursor = db.rastreiobot.find_one({
        "code": code.upper(),
        "users": user
    })
    if cursor:
        return True
    return False


# Insert package on DB
def add_package(code, user):
    print("add_package")
    stat = get_update(code)
    if stat == 0:
        return stat
    elif stat == 2:
        return stat
    else:
        stats = []
        stats.append(str(u'\U0001F4EE') + ' <b>' + code + '</b>')
        if stat == 1:
            stats.append('Aguardando recebimento pela ECT.')
            stat = stats
            db.rastreiobot.insert_one({
                "code": code.upper(),
                "users": [user],
                "stat": stat,
                "time": str(time())
            })
        stat = 10
    return stat


# Add a user to a package that exists on DB
def add_user(code, user):
    print("add_user")
    db.rastreiobot.update_one({
        "code": code.upper()}, {
        "$push": {
            "users": user
        }
    })


def del_user(chatid, code):
    cursor = db.rastreiobot.find()
    for elem in cursor:
        if str(chatid) in elem['users']:
            array = elem['users']
            array.remove(str(chatid))
    db.rastreiobot.update_one({
        "code": code.upper()}, {
        "$set": {"users": array}
    })


# Set a description to a package
def set_desc(code, user, desc):
    if not desc:
        desc = code
    db.rastreiobot.update_one({
        "code": code.upper()}, {
        "$set": {user: desc}
    })


def check_system():
    try:
        url = ('http://webservice.correios.com.br/')
        response = requests.get(url, timeout=3)
    except Exception:
        return False
    print(str(response))
    if '200' in str(response):
        return True
    else:
        return False


# Update package tracking state
def get_update(code):
    return check_update(code)


# Add to log
def log_text(chatid, message_id, text):
    logger_info.info(
        str(datetime.now()) +
        '\t' + str(chatid) + ' \t' +
        str(message_id) + ' \t' + str(text)
    )


@bot.message_handler(commands=['Repetir', 'Historico'])
def echo_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    if int(message.chat.id) > 0:
        send_clean_msg(bot, message.chat.id, msgs.user)
    else:
        send_clean_msg(bot, message.chat.id, msgs.group)


@bot.message_handler(commands=['pacotes', 'Pacotes'])
def echo_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    chatid = message.chat.id
    message, qtd = list_packages(chatid, False)
    if qtd == 0:
        message = msgs.not_found
    elif qtd == -1:
        message = msgs.error_bot
    else:
        message = '<b>Clique para ver o histórico:</b>\n' + message
        if len(message) > 4000:
            message = message[0:4000]
    if qtd > 7 and str(chatid) not in PATREON:
        message = message + msgs.patreon
    send_clean_msg(bot, chatid, message)


@bot.message_handler(commands=['concluidos', 'Concluidos'])
def echo_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    chatid = message.chat.id
    message, qtd = list_packages(chatid, True)
    if len(message) < 1:
        message = msgs.not_found
    else:
        message = '<b>Pacotes concluídos nos últimos 30 dias:</b>\n' + message
    if qtd > 12 and str(chatid) not in PATREON:
        message = message + msgs.patreon
    bot.send_message(chatid, message, parse_mode='HTML')


@bot.message_handler(commands=['status', 'Status'])
def echo_all(message):
    log_text(
        message.chat.id,
        message.message_id,
        message.text + '\t' + str(message.from_user.first_name)
    )
    with open(LOG_ALERTS_FILE) as f:
        today = (sum(1 for _ in f))
    str_yesterday = datetime.now() - timedelta(1)
    str_yesterday = str_yesterday.strftime('%Y-%m-%d')
    try:
        with open(LOG_ALERTS_FILE + '.' + str_yesterday) as f:
            yesterday = (sum(1 for _ in f))
    except Exception:
        yesterday = ''
    qtd, wait = count_packages()
    chatid = message.chat.id
    bot.send_message(
        chatid, str(u'\U0001F4EE') + '<b>@RastreioBot</b>\n\n' +
        'Pacotes em andamento: ' + str(qtd) + '\n' +
        'Pacotes em espera: ' + str(wait) + '\n\n' +
        'Alertas enviados hoje: ' + str(today) + '\n' +
        'Alertas enviados ontem: ' + str(yesterday),
        parse_mode='HTML'
    )


@bot.message_handler(commands=['info', 'Info', 'help', 'Help'])
def echo_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    log_text(
        message.chat.id,
        message.message_id,
        message.text + '\t' +
        str(message.from_user.first_name)
    )
    chatid = message.chat.id
    ads = open('ad.txt').read().splitlines()
    ad = random.choice(ads)
    ad = ad.replace(';', '\n')
    bot.send_message(
        chatid, msgs.howto + ad + '\n\n@GabrielRF',
        disable_web_page_preview=True, parse_mode='HTML'
    )


@bot.message_handler(commands=['del', 'Del', 'remover', 'apagar'])
def echo_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    log_text(
        message.chat.id,
        message.message_id,
        message.text + '\t' + str(message.from_user.first_name)
    )
    try:
        code = message.text.split(' ')[1]
        code = code.replace('@', ' ')
        del_user(message.chat.id, code)
        bot.send_message(message.chat.id, 'Pacote removido.')
    except Exception:
        bot.send_message(message.chat.id, msgs.remove, parse_mode='HTML')


@bot.message_handler(content_types=['document', 'audio', 'photo'])
def echo_all(message):
    bot.reply_to(message, 'Formato inválido')
    log_text(message.chat.id, message.message_id, 'Formato inválido')


# entry point for adding a tracking number
@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    log_text(message.chat.id, message.message_id, message.text)
    user = str(message.chat.id)
    code = (
        str(message.text.replace('/start ', '').split(' ')[0])
        .replace('/', '').upper().replace('@RASTREIOBOT', '')
    )
    try:
        desc = str(message.text.split(' ', 1)[1])
    except Exception:
        desc = code
        # aqui vou separar em dois tipo de rastreio
    if check_type(code) is not None:
        exists = check_package(code)
        if exists:
            exists = check_user(code, user)
            if not exists:
                add_user(code, user)
            status = status_package(code)
            message = ''
            system = check_system()
            for status in status_package(code):
                message = message + '\n\n' + status
            if not system:
                message = (message + msgs.error_sys)
            if int(user) > 0:
                bot.send_message(
                    user,
                    message,
                    parse_mode='HTML',
                    reply_markup=markup_btn
                )
            else:
                send_clean_msg(bot, user, message)
            if desc != code:
                set_desc(str(code), str(user), desc)
        else:
            stat = add_package(str(code), str(user))
            if stat == 0:
                bot.reply_to(message, 'Correios fora do ar')
            if stat == 2:
                bot.reply_to(message, msgs.typo)
            elif stat == 1:
                bot.reply_to(message, msgs.not_found)
            elif stat == 10:
                set_desc(str(code), str(user), desc)
                if int(message.chat.id) > 0:
                    bot.reply_to(
                        message,
                        'Pacote cadastrado.',
                        reply_markup=markup_btn
                    )
                else:
                    bot.reply_to(
                        message,
                        'Pacote cadastrado.',
                        reply_markup=markup_clean
                    )
                status = status_package(code)
                last = len(status) - 1
                if int(user) > 0:
                    bot.send_message(
                        user,
                        status_package(code)[last],
                        parse_mode='HTML',
                        reply_markup=markup_btn
                    )
                else:
                    send_clean_msg(bot, user, status_package(code)[last])
    elif code == 'START':
        if int(message.chat.id) > 0:
            send_clean_msg(bot, message.chat.id, msgs.user)
        else:
            send_clean_msg(bot, message.chat.id, msgs.group)
    else:
        if int(user) > 0:
            bot.reply_to(message, msgs.typo)


bot.polling()
