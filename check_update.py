import configparser
import json
import requests
from bs4 import BeautifulSoup

config = configparser.ConfigParser()
config.sections()
config.read('bot.conf')

usuario = config['CORREIOS']['usuario']
senha = config['CORREIOS']['senha']
token = config['CORREIOS']['token']

def check_update(code, max_retries=3):
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

    result = json.loads(response)
    tabela = result['objeto'][0]['evento']

    stats.append(str(u'\U0001F4EE') + ' <b>' + code + '</b>')

    if len(tabela) < 1:
        print('Codigo não encontrado')
        mensagem = 'Aguardando recebimento pelo ECT.'
        stats.append(mensagem)
        return 1

    for evento in reversed(tabela):
        # print(index)
        data = evento['data'] + ' ' + evento['hora']
        # print(data)
        local = evento['unidade']['local']
        situacao = evento['descricao']
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
    # for elem in stats:
        # print(elem)
        # print('-')
    return stats
