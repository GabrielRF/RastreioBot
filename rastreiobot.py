import configparser
import logging.handlers
import random
import webhook
from datetime import datetime, timedelta
from time import time

import requests
import sentry_sdk
import telebot

import apis.apicorreios as correios
from utils.misc import check_type, send_clean_msg, check_package, check_update
from telebot import types
import utils.msgs as msgs
import utils.status as status
from rastreio import db

config = configparser.ConfigParser()
config.read('bot.conf')

TOKEN = config['RASTREIOBOT']['TOKEN']
int_check = int(config['RASTREIOBOT']['int_check'])
LOG_INFO_FILE = config['RASTREIOBOT']['text_log']
LOG_ROUTINE_FILE = config['RASTREIOBOT']['routine_log']
LOG_ALERTS_FILE = config['RASTREIOBOT']['alerts_log']
PATREON = config['RASTREIOBOT']['patreon']
BANNED = config['RASTREIOBOT']['banned']

logger_info = logging.getLogger('InfoLogger')
logger_info.setLevel(logging.DEBUG)
handler_info = logging.handlers.TimedRotatingFileHandler(
    LOG_INFO_FILE, when='midnight', interval=1, backupCount=7, encoding='utf-8'
)
logger_info.addHandler(handler_info)

bot = telebot.TeleBot(TOKEN)

markup_btn = types.ReplyKeyboardMarkup(resize_keyboard=True)
markup_btn.row('/Pacotes','/Resumo')
markup_btn.row('/Info','/Concluidos')
markup_clean = types.ReplyKeyboardRemove(selective=False)


# Count packages
def count_packages():
    cursor = db.all_packages()
    qtd = 0
    wait = 0
    extraviado = 0
    despacho = 0
    sem_imposto = 0
    importado = 0
    tributado = 0
    trackingmore = 0
    for elem in cursor:
        if len(elem['code']) > 13:
            trackingmore = trackingmore + 1
        if 'Aguardando recebimento pel' in str(elem):
            wait = wait + 1
        else:
            qtd = qtd + 1
        if 'Aguardando pagamento do despacho postal' in str(elem):
            despacho = despacho + 1
        if 'Liberado sem tributação' in str(elem):
            sem_imposto = sem_imposto + 1
        if 'Objeto recebido pelos Correios do Brasil' in str(elem):
            importado = importado + 1
        if 'Fiscalização Aduaneira finalizada' in str(elem):
            tributado = tributado + 1
        if 'Objeto roubado' in str(elem):
            extraviado = extraviado + 1
    return qtd, wait, despacho, sem_imposto, importado, tributado, trackingmore, extraviado


def package_status_can_change(package):
    current_status = package['stat'][-1].lower()
    return all([
        'objeto entregue ao' not in current_status,
        'objeto apreendido' not in current_status,
        'objeto roubado' not in current_status,
        'delivered' not in current_status,
        'objeto devolvido ao remet' not in current_status,
    ])


## List packages of a user
def list_packages(chatid, done, status):
    aux = ''
    try:
        cursor = db.search_packages_per_user(chatid)
        qtd = 0
        for elem in cursor:
            if str(chatid) in elem['users']:
                try:
                    len(elem['stat'])
                except Exception:
                    elem['stat'] = ['Sistema fora do ar']
                if not done:
                    if package_status_can_change(elem):
                        if status:
                            aux = aux + str(u'\U0001F4EE') + '<code>' + elem['code'] + '</code>'
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
                    if not package_status_can_change(elem):
                        aux = aux + elem['code']
                        try:
                            if elem[str(chatid)] != elem['code']:
                                aux = aux + ' <b>' + elem[str(chatid)] + '</b>'
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


# Insert package on DB
def add_package(code, user):
    code = code.upper()
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
        elif stat == status.NOT_FOUND_TM:
            stats.append('Verificando com as possíveis transportadoras. Por favor, aguarde.')
            stat = stats
        db.add_package(code, user, stat)
        stat = status.OK
    return stat


def check_system_correios():
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
        ' ' + str(chatid) + ' \t' +
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
    if str(message.from_user.id) in BANNED:
         log_text(message.chat.id, message.message_id, '--- BANIDO --- ' + message.text)
         bot.send_message(message.chat.id, msgs.banned)
         return 0
    chatid = message.chat.id
    message, qtd = list_packages(chatid, False, False)
    if qtd == 0:
        send_clean_msg(bot, chatid, msgs.not_found)
    elif qtd == -1:
        send_clean_msg(bot, chatid, msgs.error_bot)
    else:
        message = '<b>Clique para ver o histórico:</b>\n' + message
        msg_split = message.split('\n')
        for elem in range(0, len(msg_split)-1, 10):
             s = '\n'
             bot.send_message(chatid,
                 s.join(msg_split[elem:elem+10]), parse_mode='HTML',
                 reply_markup=markup_clean, disable_web_page_preview=True)

        try:
            subscriber = webhook.select_user('chatid', chatid)[1]
        except TypeError:
            subscriber = ''
        if qtd > 7 and chatid > 0 and str(chatid) not in PATREON and str(chatid) not in subscriber:
            bot.send_message(chatid,
                str(u'\U0001F4B5') + '<b>Colabore!</b>'
                + '\nPicPay: http://grf.xyz/picpay',
                parse_mode='HTML', reply_markup=markup_clean,
                disable_web_page_preview=True)


@bot.message_handler(commands=['resumo', 'Resumo'])
def cmd_resumo(message):
    bot.send_chat_action(message.chat.id, 'typing')
    if str(message.from_user.id) in BANNED:
        log_text(message.chat.id, message.message_id, '--- BANIDO --- ' + message.text)
        bot.send_message(message.chat.id, msgs.banned)
        return 0
    chatid = message.chat.id
    message, qtd = list_packages(chatid, False, True)
    if qtd == 0:
        message = msgs.not_found
    elif qtd == -1:
        message = msgs.error_bot
    else:
        message = '<b>Resumo dos pacotes:</b>\n\n' + message
        if len(message) > 3000:
            message = 'Muitos pacotes cadastrados para utilizar tal função.\nPor favor, envie /Pacotes.'
    bot.send_message(chatid, message, parse_mode='HTML', reply_markup=markup_clean, disable_web_page_preview=True)


@bot.message_handler(commands=['concluidos', 'Concluidos'])
def cmd_concluidos(message):
    bot.send_chat_action(message.chat.id, 'typing')
    if str(message.from_user.id) in BANNED:
        log_text(message.chat.id, message.message_id, '--- BANIDO --- ' + message.text)
        bot.send_message(message.chat.id, msgs.banned)
        return 0
    chatid = message.chat.id
    message, qtd = list_packages(chatid, True, False)
    if len(message) < 1:
        bot.send_message(chatid, msgs.not_found, parse_mode='HTML', disable_web_page_preview=True)
    else:
        message = '<b>Pacotes concluídos nos últimos 30 dias:</b>\n' + message
        msg_split = message.split('\n')
        for elem in range(0, len(msg_split)-1, 10):
            s = '\n'
            bot.send_message(chatid,
                s.join(msg_split[elem:elem+10]), parse_mode='HTML',
                reply_markup=markup_clean, disable_web_page_preview=True)


@bot.message_handler(commands=['status', 'Status'])
def cmd_status(message):
    bot.send_chat_action(message.chat.id, 'typing')
    if str(message.from_user.id) in BANNED:
        log_text(message.chat.id, message.message_id, '--- BANIDO --- ' + message.text)
        bot.send_message(message.chat.id, msgs.banned)
        return 0
    log_text(
        message.chat.id,
        message.message_id,
        message.text + '\t' + str(message.from_user.first_name)
    )

    qtd, wait, despacho, sem_imposto, importado, tributado, trackingmore, extraviado = count_packages()
    chatid = message.chat.id
    bot.send_message(
        chatid, str(u'\U0001F4EE') + '<b>@RastreioBot</b>\n\n' +
        'Quantidade de pacotes: ' + str(qtd+wait) + '\n\n'
        'Pacotes em andamento: ' + str(qtd) + '\n' +
        'Pacotes em espera: ' + str(wait) + '\n' +
        'Pacotes roubados: ' + str(extraviado) + '\n\n' +
        'Pacotes importados: ' + str(importado) + '\n' +
        'Taxados em R$15: ' + str(round(100*despacho/importado, 2)) + '%\n\n' +
        #'Pacotes sem tributação: ' + str(round(100*sem_imposto/importado, 2)) + '%\n' +
        #'Pacotes tributados: ' + str(round(100*tributado/importado, 2)) + '%\n\n'
        '<code>Estatísticas de todos os pacotes em andamento ou entregues nos últimos 30 dias</code>',
        parse_mode='HTML'
    )


@bot.message_handler(commands=['statusall', 'Statusall'])
def cmd_statusall(message):
    bot.send_chat_action(message.chat.id, 'typing')
    if str(message.from_user.id) in BANNED:
        log_text(message.chat.id, message.message_id, '--- BANIDO --- ' + message.text)
        bot.send_message(message.chat.id, msgs.banned)
        return 0
    log_text(
        message.chat.id,
        message.message_id,
        message.text + '\t' + str(message.from_user.first_name)
    )

    str_yesterday = datetime.now() - timedelta(1)
    str_yesterday = str_yesterday.strftime('%Y-%m-%d')

    with open(LOG_INFO_FILE) as f:
        todaymsg = (sum(1 for _ in f))
    try:
        with open(LOG_INFO_FILE + '.' + str_yesterday) as f:
            yesterdaymsg = (sum(1 for _ in f))
    except Exception:
            yesterdaymsg = ''

    with open(LOG_ALERTS_FILE) as f:
        today = (sum(1 for _ in f))
    try:
        with open(LOG_ALERTS_FILE + '.' + str_yesterday) as f:
            yesterday = (sum(1 for _ in f))
    except Exception:
        yesterday = ''
    qtd, wait, despacho, sem_imposto, importado, tributado, trackingmore, extraviado = count_packages()
    chatid = message.chat.id
    bot.send_message(
        chatid, str(u'\U0001F4EE') + '<b>@RastreioBot</b>\n\n' +
        'Quantidade de pacotes: ' + str(qtd+wait) + '\n\n'
        'Pacotes em andamento: ' + str(qtd) + '\n' +
        'Pacotes em espera: ' + str(wait) + '\n' +
        'Pacotes roubados: ' + str(extraviado) + '\n\n' +
        'Pacotes importados: ' + str(importado) + '\n' +
        'TrackingMore: ' + str(trackingmore) + '\n' +
        'Taxados em R$15: ' + str(round(100*despacho/importado, 2)) + '%\n' +
        'Pacotes sem tributação: ' + str(round(100*sem_imposto/importado, 2)) + '%\n\n' +
        #'Pacotes tributados: ' + str(round(100*tributado/importado, 2)) + '%\n\n' +
        'Mensagens recebidas hoje: ' + str(todaymsg) + '\n' +
        'Mensagens recebidas ontem: ' + str(yesterdaymsg) + '\n\n' +
        'Alertas enviados hoje: ' + str(today) + '\n' +
        'Alertas enviados ontem: ' + str(yesterday),
        parse_mode='HTML'
    )


@bot.message_handler(commands=['info', 'Info', 'help', 'Help'])
def cmd_help(message):
    bot.send_chat_action(message.chat.id, 'typing')
    if str(message.from_user.id) in BANNED:
        log_text(message.chat.id, message.message_id, '--- BANIDO --- ' + message.text)
        bot.send_message(message.chat.id, msgs.banned)
        return 0
    log_text(
        message.chat.id,
        message.message_id,
        message.text + '\t' +
        str(message.from_user.first_name)
    )
    chatid = message.chat.id
    ads = open('utils/ad.txt').read().splitlines()
    ad = random.choice(ads)
    ad = ad.replace(';', '\n')
    bot.send_message(
        chatid, msgs.howto + ad + '\n\n@GabrielRF',
        disable_web_page_preview=True, parse_mode='HTML'
    )

@bot.message_handler(commands=['assinei', 'Assinei'])
def cmd_sign(message):
    bot.send_chat_action(message.chat.id, 'typing')
    if str(message.from_user.id) in BANNED:
         log_text(message.chat.id, message.message_id, '--- BANIDO --- ' + message.text)
         bot.send_message(message.chat.id, msgs.banned)
         return 0
    log_text(
        message.chat.id,
        message.message_id,
        message.text + '\t' + str(message.from_user.first_name)
    )
    try:
        if not webhook.select_user('chatid', message.chat.id):
           if webhook.select_user('picpayid', message.text.lower().split(' ')[1].lower().replace('@', '')):
              webhook.updateuser('chatid', message.chat.id, 'picpayid', message.text.lower().split(' ')[1].replace('@', ''))
              bot.send_message(message.chat.id, msgs.conf_ok, parse_mode='HTML')
           else:
              bot.send_message(message.chat.id, msgs.premium, parse_mode='HTML')
        else:
           bot.send_message(message.chat.id, msgs.signed, parse_mode='HTML')
           #bot.send_message(message.chat.id, msgs.conf_ok, parse_mode='HTML')
    except IndexError:
        bot.send_message(message.chat.id, msgs.premium, parse_mode='HTML')

@bot.message_handler(commands=['del', 'Del', 'remover', 'apagar'])
def cmd_remove(message):
    bot.send_chat_action(message.chat.id, 'typing')
    if str(message.from_user.id) in BANNED:
        log_text(message.chat.id, message.message_id, '--- BANIDO --- ' + message.text)
        bot.send_message(message.chat.id, msgs.banned)
        return 0
    log_text(
        message.chat.id,
        message.message_id,
        message.text + '\t' + str(message.from_user.first_name)
    )
    try:
        code = message.text.split(' ')[1]
        code = code.replace('@', ' ')
        db.remove_user_from_package(code, message.chat.id)
        bot.send_message(message.chat.id, 'Pacote removido.')
    except Exception:
        bot.send_message(message.chat.id, msgs.remove, parse_mode='HTML')
        # bot.send_document(message.chat.id, 'CgADAQADWQADuVvARjeZRuSF_fMXAg')
        try:
            bot.send_document(message.chat.id, 'CgADAQADWgADGu_QRo7Gbbxg4ugLAg')
        except telebot.apihelper.ApiException:
            pass


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
    if str(message.from_user.id) in BANNED:
        log_text(message.chat.id, message.message_id, '--- BANIDO --- ' + message.text)
        bot.send_message(message.chat.id, msgs.banned)
        return 0
    log_text(message.chat.id, message.message_id, message.text)
    user = str(message.chat.id)
    message_text = (
        message.text
        .replace('/start ', '')
        .replace('/', '')
        .replace('📮', '')
        .strip()
        .split()
    )

    code = code_type = None
    for word in message_text:
        if word.lower() == '@rastreiobot':
            message_text.remove(word)

        code_type = check_type(word)
        if code_type:
            code = word.upper()
            message_text.remove(word)
            break

    message_text = ' '.join(message_text)

    try:
        desc = message_text.split('Data:')[0].replace('  ','')
        if desc == '':
            desc = code
    except Exception:
        desc = code

    if code_type:
        try:
            subscriber = webhook.select_user('chatid', user)[1]
        except TypeError:
            subscriber = ''
        if code_type != correios and user not in PATREON and user not in subscriber:
            bot.reply_to(message, msgs.premium, parse_mode='HTML')
            log_text(message.chat.id, message.message_id, 'Pacote chines. Usuario nao assinante.')
            return 0
        exists = check_package(code)
        if exists:
            if not db.package_has_user(code, user):
                db.add_user_to_package(code, user)
            stats = db.package_status(code)
            message = ''
            system = check_system_correios()
            for stat in stats:
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
                db.set_package_description(code, user, desc)
        else:
            stat = add_package(str(code), str(user))
            share_button = types.InlineKeyboardMarkup()
            share_button.row(types.InlineKeyboardButton("Compartilhar", url="https://rastreiobot.xyz/?codigo=" + code))
            if stat == status.OFFLINE:
                bot.reply_to(message, 'Sistema fora do ar')
            elif stat == status.TYPO:
                bot.reply_to(message, msgs.typo)
            elif stat == status.NOT_FOUND:
                bot.reply_to(message, msgs.not_found)
            elif stat == status.NOT_FOUND_TM:
                bot.reply_to(message, msgs.not_found_tm)
            elif stat == status.OK:
                db.set_package_description(code, user, desc)
                if int(message.chat.id) > 0:
                    bot.reply_to(
                        message,
                        'Pacote cadastrado.\n\nCompartilhe usando o link abaixo:',
                        reply_markup=share_button
                    )
                    print('share')
                    if desc == code:
                        send_clean_msg(bot, user, msgs.desc)
                else:
                    bot.reply_to(
                        message,
                        'Pacote cadastrado.',
                        reply_markup=markup_clean
                    )
                sttus = db.package_status(code)
                last = len(sttus) - 1
                if int(user) > 0:
                    bot.send_message(
                        user,
                        db.package_status(code)[last],
                        parse_mode='HTML',
                        reply_markup=markup_btn,
                        disable_web_page_preview=True
                    )
                else:
                    send_clean_msg(bot, user, db.package_status(code)[last])
    elif message.text.upper() == '/START':
        if int(message.chat.id) > 0:
            send_clean_msg(bot, message.chat.id, msgs.user)
            # bot.send_document(message.chat.id, 'CgADAQADhgAD45bBRvd9d-3ACM-cAg')
            # bot.send_document(message.chat.id, 'CgADAQADTAAD9-zRRl9s8doDwrMmAg')
            # bot.send_document(message.chat.id, 'CgADAQADPgADBm7QRkzGU7UpR3JzAg')
            try:
                bot.send_document(message.chat.id, 'CgADAQADWQADGu_QRlzGc4VIGIYaAg')
            except telebot.apihelper.ApiException:
                pass
        else:
            send_clean_msg(bot, message.chat.id, msgs.group)
    else:
        if int(user) > 0:
            bot.reply_to(message, msgs.typo)
        if int(user) > 0 and len(message.text) > 25:
            send_clean_msg(bot, message.from_user.id, msgs.invalid.format(message.from_user.id))


# sentry_url = config['SENTRY']['url']
# if sentry_url:
#     sentry_sdk.init(sentry_url)

bot.polling()
