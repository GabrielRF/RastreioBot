import asyncio
import configparser
import logging.handlers
import random
from rastreio.providers.correios import Correios
import webhook
from datetime import datetime, timedelta
from collections import defaultdict

import requests
import telebot

from utils.misc import check_type, send_clean_msg, check_package
from telebot import types

import utils.msgs as msgs
import utils.status as status
from rastreio import db

config = configparser.ConfigParser()
config.read('bot.conf')

TOKEN = config['RASTREIOBOT']['TOKEN']
CORREIOS_TOKEN = config["CORREIOS"]["token"]
LOG_INFO_FILE = config['RASTREIOBOT']['text_log']
LOG_ROUTINE_FILE = config['RASTREIOBOT']['routine_log']
LOG_ALERTS_FILE = config['RASTREIOBOT']['alerts_log']
PATREON = config['RASTREIOBOT']['patreon']
BANNED = config['RASTREIOBOT']['banned']
STRIPE = config['STRIPE']['TOKEN']

logger_info = logging.getLogger('InfoLogger')
logger_info.setLevel(logging.DEBUG)
handler_info = logging.handlers.TimedRotatingFileHandler(
    LOG_INFO_FILE, when='midnight', interval=1, backupCount=7, encoding='utf-8'
)
logger_info.addHandler(handler_info)

bot = telebot.TeleBot(TOKEN)

#markup_btn = types.ReplyKeyboardRemove(selective=False)
markup_btn = types.ReplyKeyboardMarkup(resize_keyboard=True)
markup_btn.row('/Pacotes')
markup_btn.row('/Resumo', '/Agrupados')
markup_btn.row('/Info', '/Gif')
markup_clean = types.ReplyKeyboardRemove(selective=False)

meli_client_id = config['MERCADOLIVRE']['client_id']
meli_client_secret_key = config['MERCADOLIVRE']['secret_key']
meli_redirect_url = config['MERCADOLIVRE']['redirect_url']

POSTBOX = str(u'\U0001F4EE')


def count_packages():
    '''
    Count total packages and packages per status
    '''
    cursor = db.all_packages()
    pkg_status = defaultdict(int)
    for elem in cursor:
        if len(elem['code']) > 13:
            pkg_status['trackingmore'] += 1
        if 'Aguardando recebimento pel' in str(elem):
            pkg_status['wait'] += 1
        else:
            pkg_status['qtd'] += 1
        if 'Aguardando pagamento do despacho postal' in str(elem):
            pkg_status['despacho'] += 1
        if 'Liberado sem tributação' in str(elem):
            pkg_status['sem_imposto'] += 1
        if 'Objeto recebido pelos Correios do Brasil' in str(elem):
            pkg_status['importado'] += 1
        if 'Aguardando pagamento' in str(elem):
            pkg_status['tributado'] += 1
        if 'Objeto roubado' in str(elem):
            pkg_status['extraviado'] += 1
    return pkg_status


def package_status_can_change(package):
    current_status = package['stat'][-1].lower()
    return all([
        'objeto entregue ao' not in current_status,
        'objeto apreendido' not in current_status,
        'objeto roubado' not in current_status,
        'delivered' not in current_status,
        'objeto devolvido ao remet' not in current_status,
    ])

def package_link(code, desc):
    text = '<a href="https://t.me/RastreioBot?start={}">{}</a> '.format(code, desc)
    return text

def send_status_sorted(bot, chatid, case, status):
    cases = {
        1: '<b>Aguardando pagamento</b> 🔫',
        2: '<b>Pagamento confirmado</b> 💸',
        3: '<b>Aguardando recebimento pela ECT</b> 🕒',
        4: '<b>Fiscalização aduaneira finalizada</b>',
        5: '<b>Objeto em trânsito </b> 🚃',
        6: '<b>Objeto saiu para entrega ao destinatário</b> 🚚',
        7: '<b>Revisão de tributos</b> 🦁',
        8: '<b>Objeto recusado</b> ❌',
        9: '<b>Objeto exportado</b> 🛫',
        10: '<b>Entrega não realizada</b> ⚠️',
        11: '<b>Aguardando retirada</b> 🏢',
        12: '<b>Sua ação é necessária</b> ⚠️',
        13: '<b>Objeto postado</b> 📦',
        14: '<b>Devolução</b> 🔙',
        15: '<b>Aduana</b> 🏢',
        16: '<b>Recebido no Brasil</b> 🇧🇷',
        17: '<b>Carteiro não atendido</b> 🚪',
        18: '<b>Objeto não chegou à unidade</b>',
        19: '<b>Recebido na unidade de distribuição</b>',
    }
    if status:
        send_clean_msg(bot, chatid, cases.get(case) + status)

def get_packages_by_status(status, cursor, chatid):
    text = ''
    for package in cursor:
        last_status = package['stat'][-1]
        desc = package.get(str(chatid)) or package['code']
        if status in last_status:
            text = text + '\n' + package_link(package['code'], desc)
    return text

def list_by_status(chatid):
    cursor = list(db.search_packages_per_user(chatid))
    waiting_payment = get_packages_by_status('Aguardando pagamento', cursor, chatid)
    payed = get_packages_by_status('Pagamento confirmado', cursor, chatid)
    not_available = get_packages_by_status('Aguardando recebimento pela ECT', cursor, chatid)
    no_payment = get_packages_by_status('Fiscalização aduaneira finalizada', cursor, chatid)
    in_transit = get_packages_by_status('Objeto em trânsito', cursor, chatid)
    delivery = get_packages_by_status('saiu para entrega', cursor, chatid)
    tribute = get_packages_by_status('tributo', cursor, chatid)
    refused = get_packages_by_status('recusou o objeto', cursor, chatid)
    exported = get_packages_by_status('unidade de exportação', cursor, chatid)
    not_delivered = get_packages_by_status('Entrega não realizada', cursor, chatid)
    pickup = get_packages_by_status('retirada', cursor, chatid)
    waiting_action = get_packages_by_status('ação é necessária', cursor, chatid)
    posted = get_packages_by_status('Objeto postado', cursor, chatid)
    returned = get_packages_by_status('Devolução', cursor, chatid)
    customs = get_packages_by_status('aduaneira', cursor, chatid)
    received_br = get_packages_by_status('Correios do Brasil', cursor, chatid)
    not_answered = get_packages_by_status('arteiro não atendido', cursor, chatid)
    not_arrived = get_packages_by_status('Objeto ainda não chegou à unidade', cursor, chatid)
    dist_unit = get_packages_by_status('Objeto recebido na unidade de distribuição', cursor, chatid)
    try:
        send_status_sorted(bot, chatid, 1, waiting_payment)
        send_status_sorted(bot, chatid, 2, payed)
        send_status_sorted(bot, chatid, 3, not_available)
        send_status_sorted(bot, chatid, 4, no_payment)
        send_status_sorted(bot, chatid, 5, in_transit)
        send_status_sorted(bot, chatid, 6, delivery)
        send_status_sorted(bot, chatid, 7, tribute)
        send_status_sorted(bot, chatid, 8, refused)
        send_status_sorted(bot, chatid, 9, exported)
        send_status_sorted(bot, chatid, 10, not_delivered)
        send_status_sorted(bot, chatid, 11, pickup)
        send_status_sorted(bot, chatid, 12, waiting_action)
        send_status_sorted(bot, chatid, 13, posted)
        send_status_sorted(bot, chatid, 14, returned)
        send_status_sorted(bot, chatid, 15, customs)
        send_status_sorted(bot, chatid, 16, received_br)
        send_status_sorted(bot, chatid, 17, not_answered)
        send_status_sorted(bot, chatid, 18, not_arrived)
        send_status_sorted(bot, chatid, 19, dist_unit)
    except Exception:
        bot.send_message('9083329', 'Erro MongoBD.')
        qtd = -1

def list_packages(chatid, done, status):
    '''
    List all packages of a user
    '''
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
                            aux = f"{aux}{POSTBOX}<code>{elem['code']}</code>"
                        else:
                            aux = f"{aux}/{elem['code']}"
                        try:
                            if elem[str(chatid)] != elem['code']:
                                aux = f"{aux} <b>{elem[str(chatid)]}</b>"
                            if status:
                                aux = f"{aux}\n{elem['stat'][len(elem['stat'])-1]}\n"
                        except Exception:
                            pass
                        aux = f"{aux}\n"
                        qtd = qtd + 1
                else:
                    if not package_status_can_change(elem):
                        aux = f"{aux}/{elem['code']}"
                        try:
                            if elem[str(chatid)] != elem['code']:
                                aux = f"{aux} <b>{elem[str(chatid)]}</b>"
                        except Exception:
                            pass
                        aux = f"{aux}\n"
                        qtd = qtd + 1
    except Exception as e:
        bot.send_message('9083329', 'Erro MongoBD')
        print(e)
        raise
        qtd = -1
    return aux, qtd


def add_package(code, user):
    '''
    Insert package in DB
    '''
    code = code.upper()
    print("add_package")
    try:
        stat = get_update(code)
    except:
        stat = status.NOT_FOUND
    if stat in [status.OFFLINE, status.TYPO]:
        return stat
    else:
        stats = []
        stats.append(f"{POSTBOX} <b>{code}</b>")
        if stat == status.NOT_FOUND:
            stats.append('Aguardando recebimento pela ECT.')
            stat = stats
        elif stat == status.NOT_FOUND_TM:
            stats.append(
                'Verificando com as possíveis transportadoras. '
                'Por favor, aguarde.')
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
    if '200' in str(response):
        return True
    else:
        return False


def get_update(code):
    '''
    Update package tracking status
    '''
    print("get_update")
    correios = Correios(CORREIOS_TOKEN)
    retorno = asyncio.run(correios.get(code))
    print("check up: ", retorno[code])
    return retorno[code]


def log_text(chatid, message_id, text):
    '''
    Add text to log
    '''
    logger_info.info(
        str(datetime.now()) +
        ' ' + str(chatid) + ' \t' +
        str(message_id) + ' \t' + str(text)
    )


@bot.message_handler(commands=['doar', 'Doar', 'Pix', 'pix', 'PIX'])
def command_sub(message):
    log_text(message.chat.id, message.message_id, '--- DONATE --- ')
    if str(message.from_user.id) in BANNED:
         log_text(message.chat.id, message.message_id, '--- BANIDO --- ' + message.text)
         bot.send_message(message.chat.id, msgs.banned)
         return 0
    bot.send_photo(message.chat.id, 'AgACAgEAAxkBAAFvCWVfuo6kDztK_xxQVSza4gkfNPkAAYgAAjSqMRtottlFTZa3_00eUpfumRIwAAQBAAMCAAN5AAMkFwQAAR4E', caption=msgs.donate_caption, parse_mode='HTML')

bot.skip_pending = True

@bot.message_handler(commands=['Gif', 'gif'])
def cmd_repetir(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_document(message.chat.id, 'CgADAQADWQADGu_QRlzGc4VIGIYaAg')
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
    subscriber = webhook.select_user('chatid', message.chat.id)
    bot.send_chat_action(message.chat.id, 'typing')
    if str(message.from_user.id) in BANNED:
        log_text(message.chat.id, message.message_id, f'--- BANIDO --- {message.text}')
        bot.send_message(message.chat.id, msgs.banned)
        return 0
    chatid = message.chat.id
    message, qtd = list_packages(chatid, False, False)
    if qtd == 0:
        send_clean_msg(bot, chatid, msgs.not_found)
    elif qtd == -1:
        send_clean_msg(bot, chatid, msgs.error_bot)
    else:
        print(subscriber)
        msg = ''
        try:
            if int(subscriber[3]) < 0:
                msg = '\n<code>Saldo de dias de uso: ' + str(int(subscriber[3])*-1) + '</code>'
        except (ValueError, TypeError) as e:
            pass
        message = '<b>Clique para ver o histórico:</b>\n' + message
        msg_split = message.split('\n')
        for elem in range(0, len(msg_split)-1, 10):
            s = '\n'
            bot.send_message(chatid,
                s.join(msg_split[elem:elem+10]) + msg, parse_mode='HTML',
                reply_markup=markup_clean, disable_web_page_preview=True)

        try:
            subscriber = webhook.select_user('chatid', chatid)[1]
        except TypeError:
            subscriber = ''
        if qtd > 7 and chatid > 0 and str(chatid) not in subscriber:
            bot.send_message(chatid,
                str(u'\U0001F4B5') + '<b>Colabore!</b>'
                + '\nChave PIX: pix@rastreiobot.xyz',
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


@bot.message_handler(commands=['agrupados', 'Agrupados'])
def cmd_resumo(message):
    bot.send_chat_action(message.chat.id, 'typing')
    if str(message.from_user.id) in BANNED:
        log_text(message.chat.id, message.message_id, '--- BANIDO --- ' + message.text)
        bot.send_message(message.chat.id, msgs.banned)
        return 0
    chatid = message.chat.id
    list_by_status(chatid)


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

    pkg_status = count_packages()

    tax_rate = 0
    if pkg_status['importado'] > 0:
        tax_rate = round(100*pkg_status['despacho']/pkg_status['importado'], 2)

    chatid = message.chat.id
    total_packages = str(pkg_status['qtd']+pkg_status['wait'])
    bot.send_message(
        chatid,
        f"{POSTBOX} <b>@RastreioBot</b>\n\n"
        f"Quantidade de pacotes: {total_packages}\n\n"
        f"Pacotes em andamento: {str(pkg_status['qtd'])}\n"
        f"Pacotes em espera: {str(pkg_status['wait'])}\n"
        f"Pacotes roubados: {str(pkg_status['extraviado'])}\n\n"
        f"Pacotes importados: {str(pkg_status['importado'])}\n"
        f"Taxados em R$15: {str(tax_rate)}%\n\n"
        "<code>Estatísticas de todos os pacotes em andamento ou entregues nos "
        "últimos 30 dias</code>",
        parse_mode="HTML"
    )


@bot.message_handler(commands=['statusall', 'Statusall'])
def cmd_statusall(message):
    bot.send_chat_action(message.chat.id, 'typing')
    if str(message.from_user.id) in BANNED:
        log_text(
            message.chat.id,
            message.message_id,
            f'--- BANIDO --- {message.text}'
        )
        bot.send_message(message.chat.id, msgs.banned)
        return 0
    log_text(
        message.chat.id,
        message.message_id,
        f'{message.text} \t {str(message.from_user.first_name)}'
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
    pkg_status = count_packages()

    despacho_rate = 0
    tributacao_rate = 0
    if pkg_status['importado'] > 0:
        despacho_rate = round(
            100*pkg_status['despacho']/pkg_status['importado'], 2)
        tributacao_rate = round(
            100*pkg_status['tributado']/pkg_status['importado'], 2)

    chatid = message.chat.id
    total_packages = str(pkg_status['qtd']+pkg_status['wait'])
    bot.send_message(
        chatid,
        f"{POSTBOX}<b>@RastreioBot</b>\n\n"
        f"Quantidade de pacotes: {total_packages}\n\n"
        f"Pacotes em andamento: {str(pkg_status['qtd'])}\n"
        f"Pacotes em espera: {str(pkg_status['wait'])}\n"
        f"Pacotes roubados: {str(pkg_status['extraviado'])}\n\n"
        f"Pacotes importados: {str(pkg_status['importado'])}\n"
        f"TrackingMore: {str(pkg_status['trackingmore'])}\n"
        f"Taxados somente em R$15: {str(despacho_rate)}%\n"
        f"Pacotes tributados: {str(tributacao_rate)}%\n\n"
        f"Mensagens recebidas hoje: {str(todaymsg)}\n"
        f"Mensagens recebidas ontem: {str(yesterdaymsg)}\n\n"
        f"Alertas enviados hoje: {str(today)}\n"
        f"Alertas enviados ontem: {str(yesterday)}",
        parse_mode="HTML"
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

#@bot.message_handler(commands=['assinei', 'Assinei'])
#def cmd_sign(message):
#    bot.send_chat_action(message.chat.id, 'typing')
#    if str(message.from_user.id) in BANNED:
#         log_text(message.chat.id, message.message_id, '--- BANIDO --- ' + message.text)
#         bot.send_message(message.chat.id, msgs.banned)
#         return 0
#    log_text(
#        message.chat.id,
#        message.message_id,
#        message.text + '\t' + str(message.from_user.first_name)
#    )
#    try:
#        if not webhook.select_user('chatid', message.chat.id):
#            query = webhook.select_user('picpayid', message.text.lower().split(' ')[1].lower().replace('@', ''))
#            if query  and query[1] == '':
#               webhook.updateuser('chatid', message.chat.id, 'picpayid', message.text.lower().split(' ')[1].replace('@', ''))
#               bot.send_message(message.chat.id, msgs.conf_ok, parse_mode='HTML')
#            else:
#               bot.send_message(message.chat.id, msgs.premium, parse_mode='HTML')
#        else:
#           bot.send_message(message.chat.id, msgs.signed, parse_mode='HTML')
#           #bot.send_message(message.chat.id, msgs.conf_ok, parse_mode='HTML')
#    except (IndexError, AttributeError) as e:
#        bot.send_message(message.chat.id, msgs.premium, parse_mode='HTML')

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
        code = code.upper()
        db.remove_user_from_package(code, message.chat.id)
        bot.send_message(message.chat.id, 'Pacote removido.')
    except Exception:
        bot.send_message(message.chat.id, msgs.remove, parse_mode='HTML')
        try:
            bot.send_document(message.chat.id, 'CgADAQADWgADGu_QRo7Gbbxg4ugLAg')
        except telebot.apihelper.ApiException:
            pass


@bot.message_handler(content_types=['document', 'audio', 'photo', 'animation'])
def cmd_format(message):
    bot.reply_to(message, 'Formato inválido')
    bot.delete_message(message.from_user.id, message.message_id)
    # bot.reply_to(message, ('<a href="tg://user?id={}">{}</a>').format(message.from_user.id, message.from_user.first_name), parse_mode='HTML')
    send_clean_msg(bot, message.from_user.id, msgs.invalid.format(message.from_user.id))
    log_text(message.chat.id, message.message_id, 'Formato inválido')
    print(message)


@bot.message_handler(commands=['mercardolivre', 'mercado_livre', 'meli'])
def cmd_cadastro_mercado_livre(message):
    url = (
        "https://auth.mercadolivre.com.br/authorization?"
        "response_type=code&client_id={}&redirect_uri={}&state={}"
    ).format(
        meli_client_id,
        meli_redirect_url,
        message.from_user.id
    )
    bot.reply_to(message, url)


@bot.message_handler(content_types=['pinned_message'])
def on_pin(message):
    if message.chat.id > 0:
        try:
            bot.delete_message(message.from_user.id, message.message_id)
        except:
            pass

AVISO = (
    '📮 <b>@RastreioBot em manutenção</b>'
    '\n\nPor uma mudança nos Correios, o @RastreioBot não consegue mais fazer consultas.'
    '\n\n<a href="https://twitter.com/RastreioBot/status/1673751465062481920">🔗 Leia mais aqui</a>.'
    )

@bot.message_handler(func=lambda m: True)
def cmd_magic(message):
    '''
    Entry point for adding a tracking number
    '''
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, AVISO, parse_mode='HTML', disable_web_page_preview=True)
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
    )
    if '/start ' in message.text:
        message_text = message_text.replace('_', ' ')
    message_text = message_text.split()

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
    print(code)

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
        if code_type != Correios and user not in PATREON and user not in subscriber:
            bot.reply_to(message, msgs.typo, parse_mode='HTML', disable_web_page_preview=True)
            log_text(message.chat.id, message.message_id, 'Pacote chines. Usuario nao assinante.')
            return 0
        exists = check_package(code)
        if exists:
            if not db.package_has_user(code, user):
                db.add_user_to_package(code, user)
            stats = db.package_status(code)
            if desc != code:
                db.set_package_description(code, user, desc)
            try:
                desc = db.get_package_desc(code, user)
            except:
                pass
            message = ''
            system = check_system_correios()
            for stat in stats:
                message = message + '\n\n' + stat
            if not system:
                message = (message + msgs.error_sys)
            if code != desc:
                message = message.replace(f'📮', f'📮 <b>{desc}</b>\n')
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
        else:
            stat = add_package(str(code), str(user))
            share_button = types.InlineKeyboardMarkup()
            share_button.row(types.InlineKeyboardButton("Compartilhar", url="https://t.me/share/url?url=https://rastreiobot.xyz/?codigo=" + code))
            if stat == status.OFFLINE:
                bot.reply_to(message, 'Sistema fora do ar')
            elif stat == status.TYPO:
                bot.reply_to(message, msgs.typo)
                bot.delete_message(message.from_user.id, message.message_id)
            elif stat == status.NOT_FOUND:
                bot.reply_to(message, msgs.not_found)
            elif stat == status.NOT_FOUND_TM:
                bot.reply_to(message, msgs.not_found_tm)
            elif stat == status.OK:
                db.set_package_description(code, user, desc)
                if int(message.chat.id) > 0:
                    ads = open('utils/ad.txt').read().splitlines()
                    ad = random.choice(ads)
                    ad = ad.replace(';', '\n')
                    bot.reply_to(
                        message,
                        'Pacote cadastrado.\n\n' + ad + '\n\nCompartilhe usando o link abaixo:',
                        reply_markup=share_button, parse_mode='HTML', disable_web_page_preview=True
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
            bot.delete_message(message.from_user.id, message.message_id)
        if int(user) > 0 and len(message.text) > 25:
            send_clean_msg(bot, message.from_user.id, msgs.invalid.format(message.from_user.id))
        try:
            if bot.get_chat_member(message.chat.id, 102419067).status == 'administrator':
                send_clean_msg(bot, message.chat.id, msgs.not_admin)
        except:
            pass


# sentry_url = config['SENTRY']['url']
# if sentry_url:
#     sentry_sdk.init(sentry_url)

if __name__ == "__main__":
    bot.infinity_polling()
