from bs4 import BeautifulSoup
from check_update import check_update
from datetime import datetime
from time import time
from pymongo import MongoClient
from telebot import types

import configparser
import logging
import logging.handlers
import random
import requests
import sys
import telebot

config = configparser.ConfigParser()
config.sections()
config.read('bot.conf')

TOKEN = config['RASTREIOBOT']['TOKEN']
int_check = int(config['RASTREIOBOT']['int_check'])
LOG_INFO_FILE = config['RASTREIOBOT']['text_log']
PATREON = config['RASTREIOBOT']['patreon']

logger_info = logging.getLogger('InfoLogger')
logger_info.setLevel(logging.DEBUG)
handler_info = logging.handlers.TimedRotatingFileHandler(LOG_INFO_FILE,
    when='midnight', interval=1, backupCount=7, encoding='utf-8')
logger_info.addHandler(handler_info)

bot = telebot.TeleBot(TOKEN)
client = MongoClient()
db = client.rastreiobot

markup_btn = types.ReplyKeyboardMarkup(resize_keyboard=True)
markup_btn.row('/Pacotes','/Info','/Concluidos')
markup_clean = types.ReplyKeyboardRemove(selective=False)

## Check if package exists in DB
def check_package(code):
    cursor = db.rastreiobot.find_one({"code": code.upper()})
    if cursor:
        return True
    return False

## List packages of a user
def list_packages(chatid, done):
    cursor = db.rastreiobot.find()
    aux = ''
    qtd = 0
    for elem in cursor:
        if str(chatid) in elem['users']:
            if not done:
                if 'objeto entregue ao' not in elem['stat'][len(elem['stat'])-1].lower():
                    aux = aux + '/' + elem['code']
                    try:
                        if elem[str(chatid)] != elem['code']:
                            aux = aux + ' ' +  elem[str(chatid)]
                    except:
                        pass
                    aux = aux + '\n'
                    qtd = qtd + 1
            else:
                if 'objeto entregue ao' in elem['stat'][len(elem['stat'])-1].lower():
                    aux = aux + elem['code']
                    try:
                        if elem[str(chatid)] != elem['code']:
                            aux = aux + ' ' +  elem[str(chatid)]
                    except:
                        pass
                    aux = aux + '\n'
                    qtd = qtd + 1
    return aux, qtd

## Get last state of a package from DB 
def status_package(code):
    cursor = db.rastreiobot.find_one(
    {
        "code": code
    })
    return cursor['stat']

## Check if user exists on a specific tracking code
def check_user(code, user):
    cursor = db.rastreiobot.find_one(
    {
            "code": code.upper(),
            "users": user
    })
    if cursor:
        return True
    return False

## Insert package on DB
def add_package(code, user):
    # import ipdb; ipdb.set_trace()
    stat = get_update(code)
    if stat == 0:
        return stat
    elif stat == 1:
        return stat
    else:
        cursor = db.rastreiobot.insert_one (
        {
            "code" : code.upper(),
            "users" : [user],
            "stat" : stat,
            "time" : str(time())
        })
        stat = 10
    return stat

## Add a user to a package that exists on DB
def add_user(code, user):
    cursor = db.rastreiobot.update_one (
    { "code" : code.upper() },
    {
        "$push": {
            "users" : user
        }
    })

def del_user(code, user):
    cursor = db.rastreiobot.update (
    { "code" : code.upper() },
    {
        "$pull": {
            "users" : str(user)
        }
    })
    print(str(cursor))

## Set a description to a package
def set_desc(code, user, desc):
    if not desc:
        desc = code
    cursor = db.rastreiobot.update_one (
    { "code" : code.upper() },
    {
        "$set": {
            user : desc
        }
    })

def check_system():
    try:
        URL = ('http://webservice.correios.com.br/')
        response = requests.get(URL, timeout=3)
    except:
        return False
    print(str(response))
    if '200' in str(response):
        return True
    else:
        return False


## Update package tracking state
def get_update(code):
    return check_update(code)

## Add to log
def log_text(chatid, message_id, text):
    logger_info.info(
        str(datetime.now())
        + '\t' + str(chatid)
        + ' \t' + str(message_id)
        + ' \t' + str(text)
    )

@bot.message_handler(commands=['start', 'Repetir', 'Historico'])
def echo_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    chatid = message.chat.id
    mensagem = message.text
    user = (str(u'\U0001F4EE') + '<b>@RastreioBot!</b>\n\n'
        'Por favor, envie um código de objeto.\n\n' +
        'Para adicionar uma descrição, envie um código ' +
        'seguido da descrição.\n\n' +
        '<i>PN123456789BR Minha encomenda</i>')
    group = (str(u'\U0001F4EE') + '<b>@RastreioBot!</b>\n\n'
        'Por favor, envie um código de objeto.\n\n' +
        'Para adicionar uma descrição, envie um código ' +
        'seguido da descrição.\n\n' +
        '<i>/PN123456789BR Minha encomenda</i>')
    if int(message.chat.id) > 0:
        bot.send_message(message.chat.id, user, parse_mode='HTML', reply_markup=markup_clean)
    else:
        bot.send_message(message.chat.id, group, parse_mode='HTML', reply_markup=markup_clean)

@bot.message_handler(commands=['pacotes', 'Pacotes'])
def echo_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    chatid = message.chat.id
    message, qtd = list_packages(chatid, False)
    if len(message) < 1:
        message = "Nenhum pacote encontrado."
    else:
        message = '<b>Clique para ver o histórico:</b>\n' + message
    if qtd > 7 and str(chatid) not in PATREON:
        message = (
            message + '\n'
            + str(u'\U0001F4B5') + '<b>Colabore!</b>'
            + '\nhttp://grf.xyz/paypal'
        )
    bot.send_message(chatid, message, parse_mode='HTML', reply_markup=markup_clean)

@bot.message_handler(commands=['concluidos','Concluidos'])
def echo_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    chatid = message.chat.id
    message, qtd = list_packages(chatid, True)
    if len(message) < 1:
        message = "Nenhum pacote encontrado."
    else:
        message = '<b>Pacotes concluídos nos últimos 30 dias:</b>\n' + message
    if qtd > 12 and str(chatid) not in PATREON:
        message = (
            message + '\n'
            + str(u'\U0001F4B5') + '<b>Colabore!</b>'
            + '\nhttp://grf.xyz/paypal'
        )
    bot.send_message(chatid, message, parse_mode='HTML')

@bot.message_handler(commands=['info', 'Info'])
def echo_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    log_text(message.chat.id, message.message_id, message.text + '\t' + str(message.from_user.first_name))
    chatid = message.chat.id
    ads = open('ad.txt').read().splitlines()
    ad = random.choice(ads)
    ad = ad.replace(';','\n')
    bot.send_message(chatid, str(u'\U0001F4EE') + '<b>@RastreioBot</b>\n\n'
        + str(u'\U0001F579') + '<b>Instruções</b>'
        + '\nEnvie para o bot o código de rastreio seguido da descrição do pacote.'
        + '\n<code>PN123456789BR Minha encomenda</code>'
        + '\n\n' + str(u'\U00002B50') + '<b>Avalie o bot:</b>'
        + '\nhttps://telegram.me/storebot?start=rastreiobot\n\n'
        + str(u'\U0001F4D6') + '<b>Bot open source:</b>\nhttps://github.com/GabrielRF/RastreioBot'
        + '\n\n' + str(u'\U0001F680') + '<b>Conheça meus outros projetos:</b>'
        + '\nhttp://grf.xyz/telegrambr\n\n'
        + str(u'\U0001F4B5') + '<b>Colabore!</b>'
        + '\nhttp://patreon.com/gabrielrf'
        + '\nhttp://grf.xyz/paypal'
        + '\n<b>Colaboradores recorrentes recebem os alertas mais rapidamente!</b>'
        + '\n\n' + str(u'\U0001F517')  + ad
        + '\n\n@GabrielRF',
        disable_web_page_preview=True, parse_mode='HTML')

@bot.message_handler(content_types=['document', 'audio', 'photo'])
def echo_all(message):
    bot.reply_to(message, 'Formato inválido')
    log_text(message.chat.id, message.message_id, 'Formato inválido')

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    log_text(message.chat.id, message.message_id, message.text)
    user = str(message.chat.id)
    code = str(message.text.split(' ')[0]).replace('/','')
    code = code.upper()
    code = code.replace('@RASTREIOBOT', '')
    try:
        desc = str(message.text.split(' ', 1)[1])
    except:
        desc = code
    if len(code) == 13:
        cursor = db.rastreiobot.find()
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
                message = (message + '\n\n' + str(u'\U000026A0') + ' <b>Atenção</b>\n' +
                    'Sistema dos Correios indisponível.\n'+
                    'Os alertas poderão atrasar.')
            if int(user) > 0:
                bot.send_message(user, message, parse_mode='HTML', reply_markup=markup_btn)
            else:
                bot.send_message(user, message, parse_mode='HTML', reply_markup=markup_clean)
            if desc != code:
                set_desc(str(code), str(user), desc)
        else:
            stat = add_package(str(code), str(user))
            if stat == 0:
                bot.reply_to(message, 'Correios fora do ar')
            elif stat == 1:
                bot.reply_to(message,
                    'Código não foi encontrado no sistema dos Correios.\n'
                    + 'Talvez seja necessário aguardar algumas horas para'
                    + ' que esteja disponível para consultas.'
                )
            elif stat == 10:
                set_desc(str(code), str(user), desc)
                if int(message.chat.id) > 0:
                    msg = bot.reply_to(message, 'Pacote cadastrado.', reply_markup=markup_btn)
                else:
                    msg = bot.reply_to(message, 'Pacote cadastrado.', reply_markup=markup_clean)
                status = status_package(code)
                last = len(status)-1
                if int(user) > 0:
                    bot.send_message(user,
                        status_package(code)[last], parse_mode='HTML',
                        reply_markup=markup_btn
                    )
                else:
                    bot.send_message(user,
                        status_package(code)[last], parse_mode='HTML',
                        reply_markup=markup_clean
                    )
    else:
        if int(user) > 0:
            bot.reply_to(message, "Erro.\nVerifique se o código foi digitado corretamente.")

bot.polling()

