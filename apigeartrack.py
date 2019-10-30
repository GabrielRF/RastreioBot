import configparser
import json
import sys

import requests

config = configparser.ConfigParser()
config.read('bot.conf')

def getcorreioscode(carrier, code):
    url = ('https://geartrack.pt/api/{}?id={}'.format(carrier, code))
    r = requests.get(url)
    conteudo = str(r.content.decode('UTF-8'))
    a = json.loads(conteudo)
    if a['destinyId']:
        return(a['destinyId'])


def getstatus(code, retries):
    carrier = 'cainiao'
    code = 'LP00139186175797'
    url = ('https://geartrack.pt/api/{}?id={}'.format(carrier, code))
    r = requests.get(url)
    conteudo = str(r.content.decode('UTF-8'))
    a = json.loads(conteudo)
    print(formato_obj(a))

def formato_obj(json):
    stats = []
    stats.append(str(u'\U0001F4EE') + ' <b>' + json['id'] + '</b>')
    tabela = json['states']
    for evento in reversed(tabela):
        data = evento['date']
        situacao = evento['state']
        mensagem = ('Data: {}' +
            '\nSituacao: <b>{}</b>'
        ).format(data, situacao)
        stats.append(mensagem)
    if json['destinyId']:
        stats.append('Pacote recebido nos Correios.\nCódigo: /' + json['destinyId'])
    return stats


if __name__ == '__main__':
    getstatus(sys.argv[1], 0)
