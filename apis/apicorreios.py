import asyncio
import traceback
import configparser
import json
import sys
from datetime import date
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


def parse(code, tabela):
    if len(tabela) < 1:
        return []

    # stats.append(str(u'\U0001F4EE') + ' <b>' + code + '</b>')
    stats = []
    stats.append(str(u'\U0001F4EE') + '<a href="https://t.me/rastreiobot?start=' + code + '">' + code + '</a>')
    for evento in reversed(tabela):
        try:
            dia0 = int(tabela[len(tabela) - 1]['data'].split('/')[0])
            mes0 = int(tabela[len(tabela) - 1]['data'].split('/')[1])
            ano0 = int(tabela[len(tabela) - 1]['data'].split('/')[2])
            data0 = date(ano0, mes0, dia0)
            dia1 = int(evento['data'].split('/')[0])
            mes1 = int(evento['data'].split('/')[1])
            ano1 = int(evento['data'].split('/')[2])
            data1 = date(ano1, mes1, dia1)
            delta = data1 - data0
        except Exception:
            delta = 0
            pass
        #print(evento['tipo'], evento['status'])
        data = evento['data'] + ' ' + evento['hora']
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
            if 'objeto entregue ao' in situacao.lower():
                mensagem = mensagem + ' ' + str(u'\U0001F381')
            elif 'encaminhado' in situacao.lower():
                mensagem = mensagem + ' ' + str(u'\U00002197')
            elif 'postado' in situacao.lower():
                mensagem = mensagem + ' ' + str(u'\U0001F4E6')
            elif 'saiu para entrega' in situacao.lower():
                mensagem = mensagem + ' ' + str(u'\U0001F69A')
            elif 'recebido pelos correios' in situacao.lower():
                mensagem = mensagem + ' ' + str(u'\U0001F4E5')
            elif 'aguardando retirada' in situacao.lower():
                mensagem = mensagem + ' ' + str(u'\U0001F3E2')
            elif 'objeto apreendido' in situacao.lower():
                mensagem = mensagem + ' ' + str(u'\U0001F46E')
            elif 'aguardando confirmação de pagamento' in situacao.lower():
                mensagem = mensagem + ' ' + str(u'\U0001F554')
            elif 'objeto pago' in situacao.lower():
                mensagem = mensagem + ' ' + str(u'\U0001F4B8')
            elif 'aduaneira finalizada' in situacao.lower():
                mensagem = (mensagem + '\n<i>Acesse o ambiente </i>' +
                '<a href="https://apps.correios.com.br/portalimportador">Minhas Importações</a>')
            elif 'Sua ação é necessária' in situacao.lower():
                mensagem = (mensagem + '\n<i>Acesse o ambiente </i>' +
                '<a href="https://apps.correios.com.br/portalimportador">Minhas Importações</a>')
            elif 'aguardando pagamento' in situacao.lower():
                mensagem = (mensagem + ' ' + str(u'\U0001F52B') +
                '\n<i>Links para efetuar pagamentos aos Correios:</i>' +
                '\n<a href="https://www2.correios.com.br/sistemas/rastreamento/">Rastreamento</a>' +
                '\n<a href="https://apps.correios.com.br/portalimportador/">Portal Importador</a>')
            elif 'liberado sem' in situacao.lower():
                mensagem = mensagem + ' ' + str(u'\U0001F389')
        if observacao:
            mensagem = mensagem + '\nObservação: ' + observacao.strip().title()
            if 'liberado sem' in observacao.lower():
                mensagem = mensagem + ' ' + str(u'\U0001F389')
            elif 'pagamento' in observacao.lower():
                mensagem = (mensagem +
                '\nhttps://www2.correios.com.br/sistemas/rastreamento/')
        stats.append(mensagem)
        if str(evento['tipo']) in finished_status:
            if str(evento['status']) in finished_code:
                db.update_package(code, finished=True)

    return stats


def parse_multiple_codes_output(response):
    packages = {}
    for package in response["objeto"]:
        events = package.get("evento", [])
        code = package["numero"]
        packages[code] = parse(code, events)

    return packages


def parse_single_code_output(response):
    events = response["objeto"][0].get("evento", [])
    code = response["objeto"][0]["numero"]
    return parse(code, events)


def get(code, retries=0):
    print(str(code) + ' ' + str(retries))
    try:
        request_xml = '''
            <rastroObjeto>
                <usuario>{}</usuario>
                <senha>{}</senha>
                <tipo>L</tipo>
                <resultado>T</resultado>
                <objetos>{}</objetos>
                <lingua>101</lingua>
                <token>{}</token>
            </rastroObjeto>
        '''.format(usuario, senha, code, token)
        headers = {
            'Content-Type': 'application/xml',
            'Accept': 'application/json',
            'User-Agent': 'Dalvik/1.6.0 (' +
            'Linux; U; Android 4.2.1; LG-P875h Build/JZO34L)'
        }
        url = (
            'http://webservice.correios.com.br/service/rest/rastro/rastroMobile'
            #'http://webservice.correios.com.br/service/rastro/Rastro.wsdl'
        )
        response = requests.post(
            url, data=request_xml, headers=headers, timeout=3
        ).text
        print(response)
    except Exception:
        if retries > 0:
            print('-')
            return get(code, retries - 1)
        return status.OFFLINE
    if len(str(response)) < 10:
        return status.OFFLINE
    elif 'Objeto não encontrado na base de dados dos Correios.' in str(response):
        return status.NOT_FOUND
    try:
        response = json.loads(response)
        return parse_single_code_output(response)
    except json.decoder.JSONDecodeError as e:
        return status.NOT_FOUND
        #return 3

async def async_get(codes, retries=3):
    request_xml = '''
        <rastroObjeto>
            <usuario>{}</usuario>
            <senha>{}</senha>
            <tipo>L</tipo>
            <resultado>T</resultado>
            <objetos>{}</objetos>
            <lingua>101</lingua>
            <token>{}</token>
        </rastroObjeto>
    '''.format(usuario, senha, "".join(codes), token)
    headers = {
        'Content-Type': 'application/xml',
        'Accept': 'application/json',
        'User-Agent': 'Dalvik/1.6.0 (' +
        'Linux; U; Android 4.2.1; LG-P875h Build/JZO34L)'
    }
    url = (
        'http://webservice.correios.com.br/service/rest/rastro/rastroMobile'
    )
    async with aiohttp.ClientSession() as session:
        timeout = int(batch_size * 0.5) // (retries or 1)
        try:
            async with session.post(url, data=request_xml, headers=headers, timeout=timeout) as response:
                status_code = response.status
                response = await response.text()
        except asyncio.exceptions.TimeoutError:
            if retries > 0:
                await asyncio.sleep(batch_size // retries)
                return await async_get(codes, retries - 1)
            else:
                print(f"Correios timeout")
                return 99

    if status_code != 200:
        #return await async_get(code, retries - 1)
        #logger.warning(f"Correios status code {status_code}")

        return status.OFFLINE
    try:
        response = json.loads(response)
        if isinstance(codes, list):
            return parse_multiple_codes_output(response)
        else:
            return parse_single_code_output(response)
    except Exception as e:
        print("Error", code, response)
        return status.OFFLINE

if __name__ == '__main__':
    print(get(sys.argv[1], 0))
