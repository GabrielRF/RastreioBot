import asyncio
import traceback
import configparser
import json
import sys
from datetime import date, datetime
from rastreio import db

import aiohttp
import requests

from utils import status



config = configparser.ConfigParser()
config.read('bot.conf')

usuario = config['CORREIOS']['usuario']
senha = config['CORREIOS']['senha']
token = config['CORREIOS']['token']
finished_status = config['CORREIOS']['FSTATUS']
finished_code = config['CORREIOS']['FCODE']
batch_size = int(config['RASTREIOBOT']['batch_size'])
token = config['RASTREIOBOT']['TOKEN']
temporary_token = config['RASTREIOBOT']['TEMPORARY_TOKEN']
expiry_token_timestamp = float(config['RASTREIOBOT']['EXPIRY_TOKEN_TIMESTAMP'])
proxyapp_rastrear = config['RASTREIOBOT']['PROXYAPP_RASTREAR']
proxyapp_token = config['RASTREIOBOT']['PROXYAPP_TOKEN']


def set_is_finished(code: str, tabela: dict):
    try:
        evento = tabela[-1]
    except IndexError:
        return
    if str(evento['tipo']) in finished_status:
        if str(evento['status']) in finished_code:
            db.update_package(code, finished=True)
    if 'Favor desconsiderar a informação anterior' in evento['descricao']:
        db.update_package(code, finished=False)


def parse(code: str, tabela: dict) -> list:
    if len(tabela) < 1:
        return []

    # stats.append(str(u'\U0001F4EE') + ' <b>' + code + '</b>')
    stats = []
    stats.append(str(u'\U0001F4EE') +
                 '<a href="https://t.me/rastreiobot?start=' + code + '">' + code + '</a>')
    for evento in reversed(tabela):
        try:
            # tabela[0]['dtHrCriado'] = 2022-09-01 - 17:24:49
            last_event_hour = tabela[0]['dtHrCriado'].split("T")[1]
            last_event_date = datetime.strptime(tabela[0]['dtHrCriado'].split("T")[0], '%Y-%m-%d').strftime('%d-%m-%Y')

            # Gettings number of days between two dates (result of delta)
            today = date.today().strftime('%d-%m-%Y').split("-")
            split_date_from = last_event_date.split("-")
            date_from_to_count = date(day=int(split_date_from[0]), month=int(split_date_from[1]), year=int(split_date_from[2]))   
            date_to_to_count = date(day=int(today[0]), month=int(today[1]), year=int(today[2]))
            delta = abs((date_from_to_count - date_to_to_count))

        except Exception:
            delta = 0
            pass

        data = last_event_date.replace("-", "/") + ' ' + last_event_hour
        if delta.days == 1:
            data = data + ' (' + str(delta.days) + ' dia)'
        elif delta.days > 1:
            data = data + ' (' + str(delta.days) + ' dias)'
        try:
            local = evento['unidade']['local']
        except Exception:
            local = False
        situacao = evento['descricao']
        if 'endereço indicado' in evento['descricao']:
            try:
                situacao = (
                    situacao + '\n</b>' +
                    evento['unidade']['endereco']['numero'] + ' ' +
                    evento['unidade']['endereco']['logradouro'] + '\n' +
                    evento['unidade']['endereco']['bairro'] + '<b>'
                )
            except Exception:
                pass
        try:
            observacao = str(evento['destino'][0]['local'])
        except Exception:
            observacao = False
        mensagem = 'Data: ' + data.strip()
        if local:
            mensagem = mensagem + '\nLocal: ' + local.strip().title()
        if situacao:
            mensagem = (
                mensagem + '\nSituação: <b>' +
                situacao.strip() + '</b>'
            )
            situacao_lower = situacao.lower()

            if 'objeto entregue ao' in situacao_lower:
                mensagem = mensagem + ' ' + str(u'\U0001F381')
            elif 'encaminhado' in situacao_lower:
                mensagem = mensagem + ' ' + str(u'\U00002197')
            elif 'postado' in situacao_lower:
                mensagem = mensagem + ' ' + str(u'\U0001F4E6')
            elif 'saiu para entrega' in situacao_lower:
                mensagem = mensagem + ' ' + str(u'\U0001F69A')
            elif 'recebido pelos correios' in situacao_lower:
                mensagem = mensagem + ' ' + str(u'\U0001F4E5')
            elif 'aguardando retirada' in situacao_lower:
                mensagem = mensagem + ' ' + str(u'\U0001F3E2')
            elif 'objeto apreendido' in situacao_lower:
                mensagem = mensagem + ' ' + str(u'\U0001F46E')
            elif 'aguardando confirmação de pagamento' in situacao_lower:
                mensagem = mensagem + ' ' + str(u'\U0001F554')
            elif 'objeto pago' in situacao_lower:
                mensagem = mensagem + ' ' + str(u'\U0001F4B8')
            elif 'aduaneira finalizada' in situacao_lower:
                mensagem = (mensagem + '\n<i>Acesse o ambiente </i>' +
                            '<a href="https://apps.correios.com.br/portalimportador">Minhas Importações</a>')
            elif 'Sua ação é necessária' in situacao_lower:
                mensagem = (mensagem + '\n<i>Acesse o ambiente </i>' +
                            '<a href="https://apps.correios.com.br/portalimportador">Minhas Importações</a>')
            elif 'aguardando pagamento' in situacao_lower:
                mensagem = (mensagem + ' ' + str(u'\U0001F52B') +
                            '\n<i>Links para efetuar pagamentos aos Correios:</i>' +
                            '\n<a href="https://www2.correios.com.br/sistemas/rastreamento/">Rastreamento</a>' +
                            '\n<a href="https://apps.correios.com.br/portalimportador/">Portal Importador</a>')
            elif 'liberado sem' in situacao_lower:
                mensagem = mensagem + ' ' + str(u'\U0001F389')
        if observacao:
            mensagem = mensagem + '\nObservação: ' + observacao.strip().title()
            observacao_lower = observacao.lower()

            if 'liberado sem' in observacao_lower:
                mensagem = mensagem + ' ' + str(u'\U0001F389')
            elif 'pagamento' in observacao_lower:
                mensagem = (mensagem +
                            '\nhttps://www2.correios.com.br/sistemas/rastreamento/')
        stats.append(mensagem)

    return stats


def parse_multiple_codes_output(response: dict):
    packages = {}
    for package in response["objetos"]:
        events = package.get("eventos", [])
        code = package["codObjeto"]
        packages[code] = parse(code, events)
        set_is_finished(code, events)

    return packages


def parse_single_code_output(response: dict):
    events = response["objetos"][0]["eventos"]
    code = response["objetos"][0]["codObjeto"]
    set_is_finished(code, events)
    return parse(code, events)

def get_correios_token() -> str:
    """ Generate the particulary token to access the information in Correios API. """

    headers = {
    "content-type": "application/json",
    "user-agent": "Dart/2.18 (dart:io)",
    }

    data_access = {
        "requestToken": "YW5kcm9pZDtici5jb20uY29ycmVpb3MucHJlYXRlbmRpbWVudG87RjMyRTI5OTc2NzA5MzU5ODU5RTBCOTdGNkY4QTQ4M0I5Qjk1MzU3OA"
    }

    req = requests.post(url="https://proxyapp.correios.com.br/v1/app-validation", headers=headers, json=data_access)

    # TODO: Validar que realmente esta retornando o Token.
    return req.json()["token"]
    

def get(code: str, retries=0):
    global expiry_token_timestamp
    global temporary_token

    if expiry_token_timestamp <= datetime.now().timestamp():
        expiry_token_timestamp = datetime.now().timestamp() + (3 * 3600)
        temporary_token = get_correios_token()
        
    try:
        headers = {
            "content-type": "application/json",
            "user-agent": "Dart/2.18 (dart:io)",
            "app-check-token": temporary_token,
        }
        url = (
            f"{proxyapp_rastrear}/{code}"
            # 'http://webservice.correios.com.br/service/rest/rastro/rastroMobile'
            # 'http://webservice.correios.com.br/service/rastro/Rastro.wsdl'
        )
        response = requests.get(
            url=url, headers=headers, timeout=3
        )
        response_data = response.json()
    
    except Exception:
        if retries > 0:
            print('-')
            return get(code, retries - 1)
        return status.OFFLINE
    if len(str(response)) < 10:
        return status.OFFLINE

    elif 'mensagem' in str(response_data["objetos"][0]):
        return status.NOT_FOUND

    try:
        return parse_single_code_output(response.json())
    except json.decoder.JSONDecodeError as e:
        return status.NOT_FOUND


# TODO: Find a way to get many codes to do the process async. With that URL thats nos possible.
# async def async_get(codes, retries=3):
#     request_xml = '''
#         <rastroObjeto>
#             <usuario>{}</usuario>
#             <senha>{}</senha>
#             <tipo>L</tipo>
#             <resultado>T</resultado>
#             <objetos>{}</objetos>
#             <lingua>101</lingua>
#             <token>{}</token>
#         </rastroObjeto>
#     '''.format(usuario, senha, "".join(codes), token)
#     headers = {
#         'Content-Type': 'application/xml',
#         'Accept': 'application/json',
#         'User-Agent': 'Dalvik/1.6.0 (' +
#         'Linux; U; Android 4.2.1; LG-P875h Build/JZO34L)'
#     }
#     url = (
#         'http://webservice.correios.com.br/service/rest/rastro/rastroMobile'
#     )
#     async with aiohttp.ClientSession() as session:
#         timeout = int(batch_size * 0.5) // (retries or 1)
#         try:
#             async with session.post(url, data=request_xml, headers=headers, timeout=timeout) as response:
#                 status_code = response.status
#                 response = await response.text()
#         except asyncio.exceptions.TimeoutError:
#             if retries > 0:
#                 await asyncio.sleep(batch_size // retries)
#                 return await async_get(codes, retries - 1)
#             else:
#                 print(f"Correios timeout")
#                 return 99

#     if status_code != 200:
#         # return await async_get(code, retries - 1)
#         #logger.warning(f"Correios status code {status_code}")

#         return status.OFFLINE
#     try:
#         response = json.loads(response)
#         if isinstance(codes, list):
#             return parse_multiple_codes_output(response)
#         else:
#             return parse_single_code_output(response)
#     except Exception as e:
#         print("Error", codes, response)
#         return status.OFFLINE

if __name__ == '__main__':
    print(get(sys.argv[1], 0))
