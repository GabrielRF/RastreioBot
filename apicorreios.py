import configparser
import requests
import status
import sys

config = configparser.ConfigParser()
config.read('bot.conf')

usuario = config['CORREIOS']['usuario']
senha = config['CORREIOS']['senha']
token = config['CORREIOS']['token']


def get(code, retries):
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
        )
        response = requests.post(
            url, data=request_xml, headers=headers, timeout=3
        ).text
        print(response)
    except Exception:
        if retries > 0:
            return get(code, retries - 1)
        return status.OFFLINE
    if len(str(response)) < 10:
        return status.OFFLINE
    elif 'ERRO' in str(response):
        return status.NOT_FOUND
    return response

if __name__ == '__main__':
    print(get(sys.argv[1], 0))
