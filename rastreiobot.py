import logging
import logging.handlers
import random
from time import time
from datetime import datetime, timedelta

import configparser
import msgs
import status
import requests
import telebot
from check_update import check_update
from math import ceil
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
markup_btn.row('/Pacotes','/Resumo')
markup_btn.row('/Info','/Concluidos')
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
    qtd = 0
    wait = 0
    for elem in cursor:
        if 'Aguardando recebimento pel' in str(elem):
            wait = wait + 1
        else:
            qtd = qtd + 1
    return qtd, wait

  
## List packages of a user
def list_packages(chatid, done, status):
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
                            'objeto roubado' not in status_elem(elem)): # and
                            #'objeto devolvido' not in status_elem(elem)):
                        if status:
                            aux = aux +  str(u'\U0001F4EE') + elem['code']
                        else:
                            aux = aux + '/' + elem['code']
                        try:
                            if elem[str(chatid)] != elem['code']:
                                aux = aux + ' <b>' + elem[str(chatid)] + '</b>'
                            if status:
                                aux = aux + '\n' + elem['stat'][len(elem['stat'])-1] + '\n'
                        except Exception:
                            pass
                        aux = aux + '\n'
                        qtd = qtd + 1
                else:
                    if (
                            'objeto entregue ao' in status_elem(elem) or
                            'objeto apreendido' in status_elem(elem) or
                            'objeto roubado' in status_elem(elem)): # or
                            #'objeto devolvido' in status_elem(elem)):
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
    print("status_package")
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
    if stat in [status.OFFLINE, status.TYPO]:
        return stat
    else:
        stats = []
        stats.append(str(u'\U0001F4EE') + ' <b>' + code + '</b>')
        if stat == status.NOT_FOUND:
            stats.append('Aguardando recebimento pela ECT.')
            stat = stats
        db.rastreiobot.insert_one({
                "code": code.upper(),
                "users": [user],
                "stat": stat,
                "time": str(time())
        })
        stat = status.OK
    return stat


# Add a user to a package that exists on DB
def add_user(code, user):
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
        print('check_system')
    if '200' in str(response):
        return True
    else:
        return False


# Update package tracking state
def get_update(code):
    print("get_update")
    retorno = check_update(code)
    print("check up: ", retorno)
    return retorno


# Add to log
def log_text(chatid, message_id, text):
    logger_info.info(
        str(datetime.now()) +
        '\t' + str(chatid) + ' \t' +
        str(message_id) + ' \t' + str(text)
    )


@bot.message_handler(commands=['gif'])
def cmd_repetir(message):
    bot.send_chat_action(message.chat.id, 'typing')
    # bot.send_document(message.chat.id, 'CgADAQADhgAD45bBRvd9d-3ACM-cAg')
    # bot.send_document(message.chat.id, 'CgADAQADTAAD9-zRRl9s8doDwrMmAg')
    # bot.send_document(message.chat.id, 'CgADAQADPgADBm7QRkzGU7UpR3JzAg')
    bot.send_document(message.chat.id, 'CgADAQADWQADGu_QRlzGc4VIGIYaAg')
    # bot.send_document(message.chat.id, 'CgADAQADWQADuVvARjeZRuSF_fMXAg')
    bot.send_document(message.chat.id, 'CgADAQADWgADGu_QRo7Gbbxg4ugLAg')

@bot.message_handler(commands=['Repetir', 'Historico'])
def cmd_repetir(message):
    bot.send_chat_action(message.chat.id, 'typing')
    if int(message.chat.id) > 0:
        send_clean_msg(bot, message.chat.id, msgs.user)
    else:
        send_clean_msg(bot, message.chat.id, msgs.group)


@bot.message_handler(commands=['pacotes', 'Pacotes'])
def cmd_pacotes(message):
    bot.send_chat_action(message.chat.id, 'typing')
    chatid = message.chat.id
    message, qtd = list_packages(chatid, False, False)
    if qtd == 0:
        send_clean_msg(bot, chatid, msgs.not_found)
    elif qtd == -1:
        send_clean_msg(bot, chatid, msgs.error_bot)
    else:
        message = '<b>Clique para ver o histórico:</b>\n' + message
        msg = message
        msg_split = message.split('\n')
        for elem in range(0, len(msg_split), 10):
             s = '\n'
             bot.send_message(chatid,
                 s.join(msg_split[elem:elem+10]), parse_mode='HTML',
                 reply_markup=markup_clean, disable_web_page_preview=True)
        if qtd > 7 and chatid > 0:
            bot.send_message(chatid,
                str(u'\U0001F4B5') + '<b>Colabore!</b>'
                + '\nPicPay: http://grf.xyz/picpay'
                + '\nPayPal: http://grf.xyz/paypal'
                + '\nPatreon: http://grf.xyz/patreon',
                parse_mode='HTML', reply_markup=markup_clean, 
                disable_web_page_preview=True)


@bot.message_handler(commands=['resumo', 'Resumo'])
def cmd_resumo(message):
    bot.send_chat_action(message.chat.id, 'typing')
    chatid = message.chat.id
    message, qtd = list_packages(chatid, False, True)
    if qtd == 0:
        message = msgs.not_found
    elif qtd == -1:
        message = msgs.error_bot
    else:
        message = '<b>Resumo dos pacotes:</b>\n\n' + message
        msg = message
        if len(message) > 3000:
            message = 'Muitos pacotes cadastrados para utilizar tal função.\nPor favor, envie /Pacotes.'
    bot.send_message(chatid, message, parse_mode='HTML', reply_markup=markup_clean, disable_web_page_preview=True)


@bot.message_handler(commands=['concluidos', 'Concluidos'])
def cmd_concluidos(message):
    bot.send_chat_action(message.chat.id, 'typing')
    chatid = message.chat.id
    message, qtd = list_packages(chatid, True, False)
    if len(message) < 1:
        bot.send_message(chatid, msgs.not_found, parse_mode='HTML', disable_web_page_preview=True)
    else:
        message = '<b>Pacotes concluídos nos últimos 30 dias:</b>\n' + message
        msg_split = message.split('\n')
        for elem in range(0, len(msg_split), 10):
            s = '\n'
            bot.send_message(chatid,
                s.join(msg_split[elem:elem+10]), parse_mode='HTML',
                reply_markup=markup_clean, disable_web_page_preview=True)


@bot.message_handler(commands=['status', 'Status'])
def cmd_status(message):
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
def cmd_help(message):
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
def cmd_remove(message):
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
        # bot.send_document(message.chat.id, 'CgADAQADWQADuVvARjeZRuSF_fMXAg')
        bot.send_document(message.chat.id, 'CgADAQADWgADGu_QRo7Gbbxg4ugLAg')


@bot.message_handler(content_types=['document', 'audio', 'photo'])
def cmd_format(message):
    bot.reply_to(message, 'Formato inválido')
    # bot.reply_to(message, ('<a href="tg://user?id={}">{}</a>').format(message.from_user.id, message.from_user.first_name), parse_mode='HTML')
    send_clean_msg(bot, message.from_user.id, msgs.invalid.format(message.from_user.id))
    log_text(message.chat.id, message.message_id, 'Formato inválido')
    print(message)


# entry point for adding a tracking number
@bot.message_handler(func=lambda m: True)
def cmd_magic(message):
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
    if check_type(code) is not None:
        exists = check_package(code)
        if exists:
            exists = check_user(code, user)
            if not exists:
                add_user(code, user)
            statts = status_package(code)
            message = ''
            system = check_system()
            for stat in statts:
                message = message + '\n\n' + stat
            if not system:
                message = (message + msgs.error_sys)
            if int(user) > 0:
                bot.send_message(
                    user,
                    message,
                    parse_mode='HTML',
                    reply_markup=markup_btn,
                    disable_web_page_preview=True
                )
            else:
                send_clean_msg(bot, user, message)
            if desc != code:
                set_desc(str(code), str(user), desc)
        else:
            stat = add_package(str(code), str(user))
            if stat == status.OFFLINE:
                bot.reply_to(message, 'Correios fora do ar')
            elif stat == status.TYPO:
                bot.reply_to(message, msgs.typo)
            elif stat == status.NOT_FOUND:
                bot.reply_to(message, msgs.not_found)
            elif stat == status.OK:
                set_desc(str(code), str(user), desc)
                if int(message.chat.id) > 0:
                    bot.reply_to(
                        message,
                        'Pacote cadastrado.',
                        reply_markup=markup_btn
                    )
                    if desc == code:
                        send_clean_msg(bot, user, msgs.desc)
                else:
                    bot.reply_to(
                        message,
                        'Pacote cadastrado.',
                        reply_markup=markup_clean
                    )
                sttus = status_package(code)
                last = len(sttus) - 1
                if int(user) > 0:
                    bot.send_message(
                        user,
                        status_package(code)[last],
                        parse_mode='HTML',
                        reply_markup=markup_btn,
                        disable_web_page_preview=True
                    )
                else:
                    send_clean_msg(bot, user, status_package(code)[last])
    elif code == 'START':
        if int(message.chat.id) > 0:
            send_clean_msg(bot, message.chat.id, msgs.user)
            # bot.send_document(message.chat.id, 'CgADAQADhgAD45bBRvd9d-3ACM-cAg')
            # bot.send_document(message.chat.id, 'CgADAQADTAAD9-zRRl9s8doDwrMmAg')
            # bot.send_document(message.chat.id, 'CgADAQADPgADBm7QRkzGU7UpR3JzAg')
            bot.send_document(message.chat.id, 'CgADAQADWQADGu_QRlzGc4VIGIYaAg')
        else:
            send_clean_msg(bot, message.chat.id, msgs.group)
    else:
        if int(user) > 0:
            bot.reply_to(message, msgs.typo)


bot.polling()
