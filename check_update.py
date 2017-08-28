import configparser
import json
import requests
import re
from bs4 import BeautifulSoup
from datetime import date

config = configparser.ConfigParser()
config.sections()
config.read('bot.conf')

usuario = config['CORREIOS']['usuario']
senha = config['CORREIOS']['senha']
token = config['CORREIOS']['token']

def check_update(code, max_retries=3):
    regexp = r"^[A-Za-z]{2}\d{9}[A-Za-z]{2}$"
    if not (re.search(regexp, code)):
        return 2
    stats = []
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
            'User-Agent': 'Dalvik/1.6.0 (Linux; U; Android 4.2.1; LG-P875h Build/JZO34L)'
        }
        URL = ('http://webservice.correios.com.br/service/rest/rastro/rastroMobile')
        response = requests.post(URL, data=request_xml, headers=headers, timeout=3).text
    except:
        if max_retries > 0:
            return check_update(code, max_retries-1)
        return 0
    if len(str(response)) < 10:
        return 0
    elif 'ERRO' in str(response):
        return 1
    try:
        result = json.loads(response)
        tabela = result['objeto'][0]['evento']
    except:
        return 3

    if len(tabela) < 1:
        return 1
    stats.append(str(u'\U0001F4EE') + ' <b>' + code + '</b>')
    for evento in reversed(tabela):
        try:
            dia0 = int(tabela[len(tabela)-1]['data'].split('/')[0])
            mes0 = int(tabela[len(tabela)-1]['data'].split('/')[1])
            ano0 = int(tabela[len(tabela)-1]['data'].split('/')[2])
            data0 = date(ano0, mes0, dia0)
            dia1 = int(evento['data'].split('/')[0])
            mes1 = int(evento['data'].split('/')[1])
            ano1 = int(evento['data'].split('/')[2])
            data1 = date(ano1, mes1, dia1)
            delta = data1 - data0
        except:
            delta = 0
            pass
        data = evento['data'] + ' ' + evento['hora']
        if delta.days == 1:
            data = data + ' (' + str(delta.days)  + ' dia)'
        elif delta.days > 1:
            data = data + ' (' + str(delta.days)  + ' dias)'
        try:
            local = evento['unidade']['local']
        except:
            local = False
        situacao = evento['descricao']
        if 'endereço indicado' in evento['descricao']:
            try:
                situacao = (situacao + '\n</b>' +
                evento['unidade']['endereco']['numero'] + ' '
                + evento['unidade']['endereco']['logradouro'] + '\n'
                + evento['unidade']['endereco']['bairro'] + '<b>'
                )
            except:
                pass
        try:
            observacao =str(evento['destino'][0]['local'])
        except:
            observacao = False
        mensagem = 'Data: ' + data.strip()
        if local:
            mensagem = mensagem + '\nLocal: ' + local.strip()
        if situacao:
            mensagem = (mensagem + '\nSituação: <b>' +
                situacao.strip() + '</b>')
            if 'objeto entregue ao' in situacao.lower():
                mensagem = mensagem + ' ' + str(u'\U0001F381')
            elif 'encaminhado' in situacao.lower():
                mensagem = mensagem + ' ' + str(u'\U00002197')
            elif 'postado' in situacao.lower():
                mensagem = mensagem + ' ' + str(u'\U0001F4E6')
        if observacao:
            mensagem = mensagem + '\nObservação: ' + observacao.strip()
            if 'liberado sem' in observacao.lower():
                mensagem = mensagem + ' ' + str(u'\U0001F389')
        stats.append(mensagem)
    return stats
