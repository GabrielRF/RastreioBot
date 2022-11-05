import asyncio
import configparser
import json
import sys
from datetime import date
from datetime import datetime
from pymongo import ASCENDING, MongoClient
from rastreio import db

import requests

from utils import status

config = configparser.ConfigParser()
config.read('bot.conf')

token = config['CORREIOS']['token']
client = MongoClient()
db = client.rastreiobot

def get_request_token(token=token):
    headers = {
        "content-type": "application/json",
        "user-agent": "Dart/2.18 (dart:io)",
    }
    data_access = {
        "requestToken": token
    }
    req = requests.post(
        url="https://proxyapp.correios.com.br/v1/app-validation",
        headers=headers, json=data_access
    )

    if 200 <= req.status_code < 300:
        TOKEN_CORREIOS = req.json()['token']
    else:
        TOKEN_CORREIOS = False
    db.token.update_one(
        {"token": "app-check-token"},
        {"$set": {
            "value": TOKEN_CORREIOS,
            "last_update": datetime.now()
        } }
    )
    return TOKEN_CORREIOS

def get_package_events(code):
    header = {
        "content-type": "application/json",
        "user-agent": "Dart/2.18 (dart:io)",
        "app-check-token":
            db.token.find_one({'token': 'app-check-token'})['value'],
    }
    data_token = {
        "requestToken": token
    }
    response = requests.get(
        f'https://proxyapp.correios.com.br/v1/sro-rastro/{code}',
        headers = header
    )
    return format_object(response)

def add_emojis(text):
    casos = {
        'Objeto saiu para entrega ao destinatário': '🚚',
        'Objeto entregue ao destinatário': '🎁',
        'Objeto recebido pelos Correios do Brasil': '📥',
        'Objeto aguardando retirada no endereço indicado': '🏢',
        'Objeto encaminhado para fiscalização aduaneira de exportação': '↗️',
        'Objeto postado': '📦',
        'Liberado sem tributação': '🎉',
        'Aguardando pagamento do despacho postal': '🔫',
        'Pagamento confirmado': '💸',
        'Objeto apreendido por órgão de fiscalização': '👮',
        'Objeto dispensado do pagamento de impostos': '🎉',
        'Aguardando pagamento': '💳\n<a href="https://www.correios.com.br">Acesse o site dos Correios para fazer o pagamento</a>',
    }
    if casos.get(text):
        return f'{text} {casos.get(text)}'
    return text

def format_object(data):
    if 'SRO-020' in str(data.json()['objetos'][0]):
        return status.NOT_FOUND
    stats = []
    stats.append(str(u'\U0001F4EE') +
        '<a href="https://t.me/rastreiobot?start=' +
        data.json()['objetos'][0]['codObjeto'] +
        '">' + data.json()['objetos'][0]['codObjeto'] + '</a>')
    start_date = datetime.strptime(
        data.json()['objetos'][0]['eventos'][-1]["dtHrCriado"],
        '%Y-%m-%dT%H:%M:%S'
    )
    for evento in reversed(data.json()['objetos'][0]['eventos']):
        data = datetime.strptime(evento["dtHrCriado"], '%Y-%m-%dT%H:%M:%S')
        data_delta = data - start_date
        data = data.strftime('%d/%m/%Y %H:%M')
        if data_delta.days > 0:
            data = f'{data} ({data_delta.days} dias)'
        try:
            local = f'{evento["unidade"]["nome"].title()}'
        except KeyError:
            local = (f'{evento["unidade"]["tipo"]}'+
            f'{evento["unidade"]["endereco"]["cidade"].title()}'+
            f'{evento["unidade"]["endereco"]["uf"]}'
        )
        situacao = evento['descricao']
        try:
            observacao = (
                f'{evento["unidadeDestino"]["endereco"]["cidade"].title()}'+
                f'{evento["unidadeDestino"]["endereco"]["uf"]}'
            )
        except KeyError:
            observacao = False
        if 'Objeto aguardando retirada no endereço indicado' in situacao:
            observacao = (
                f'{evento["unidade"]["endereco"]["bairro"]}'+
                f'{evento["unidade"]["endereco"]["complemento"]}'+
                f'{evento["unidade"]["endereco"]["logradouro"]}'+
                f'{evento["unidade"]["endereco"]["numero"]}'
            )
        situacao = add_emojis(situacao)
        message = f'Data: {data}\nLocal: {local}'
        if situacao: message = f'{message}\nSituação: {situacao}'
        if observacao: message = f'{message}\nObservação: {observacao}'
        stats.append(message)
    return stats

def should_update_token():
    last = db.token.find_one({'token': 'app-check-token'})['last_update']
    diff = (datetime.now() - last).seconds
    if diff > 12*60*60:
        return True
    return False

def get(code, retries=3):
    if should_update_token():
        if not get_request_token():
            return status.OFFLINE
    return get_package_events(code)

if __name__ == '__main__':
    print(get(sys.argv[1], 0))
