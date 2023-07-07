import asyncio
import configparser
import json
import sys
from datetime import date
from datetime import datetime
from pymongo import ASCENDING, MongoClient
from rastreio import db

import aiohttp
import requests
import hashlib # Para calcular o sign

from utils import status

config = configparser.ConfigParser()
config.read('bot.conf')

token = config['CORREIOS']['token']
client = MongoClient()
db = client.rastreiobot

#Função para calcular o sign
def generate_sign(token):
    data = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    sign = hashlib.md5(f'requestToken{token}data{data}'.encode()).hexdigest()
    return data, sign

def get_request_token(token=token):
    headers = {
        "content-type": "application/json",
        "user-agent": "Dart/2.18 (dart:io)",
    }

    for i in range(5):  # tentativa de obter o token = 5x
        data, sign = generate_sign(token)

        data_access = {
            "requestToken": token,
            "data": data,
            "sign": sign
        }

        response = requests.post(
            url="https://proxyapp.correios.com.br/v1/app-validation",
            headers=headers, json=data_access
        )

        if 200 <= response.status_code < 300:
            token_correios = response.json().get('token', None)
            if token_correios is not None:
                # Caso tenha um token, adiciona ao database
                db.token.update_one(
                    {"token": "app-check-token"},
                    {"$set": {
                        "value": token_correios,
                        "last_update": datetime.now()
                    } }
                )
                return token_correios

        # Caso falhe, de um sleep e retorne a tentativa
        time.sleep(1)

    # Caso nao obtenha o token ao fim de 5 tentativas, retornar um erro
    raise ValueError("Não foi possível obter um token válido nos Correios após 5 tentativas")


def get_package_events(code):
    header = {
        "content-type": "application/json",
        "user-agent": "Dart/2.18 (dart:io)",
        "app-check-token":
            db.token.find_one({'token': 'app-check-token'})['value'],
    }
    response = requests.get(
        f'https://proxyapp.correios.com.br/v1/sro-rastro/{code}',
        headers = header
    )
    return format_object(response)

async def async_get(code, retries=3):
    code = code[0]
    if should_update_token():
        if not get_request_token():
            return status.OFFLINE
    header = {
        "content-type": "application/json",
        "user-agent": "Dart/2.18 (dart:io)",
        "app-check-token":
            db.token.find_one({'token': 'app-check-token'})['value'],
    }
    url = f'https://proxyapp.correios.com.br/v1/sro-rastro/{code}'
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=header, timeout=3) as response:
                status_code = response.status
                response = await response.text()
        except asyncio.exceptions.TimeoutError:
            if retries > 0:
                await asyncio.sleep(5)
                return await async_get(code, retries - 1)
            else:
                print(f"Correios timeout")
                return 99
    if status_code != 200:
        return status.OFFLINE
    try:
        response = json.loads(response)
        return format_object(response)
    except Exception as e:
        print("Error", code, response)
        return status.OFFLINE

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
