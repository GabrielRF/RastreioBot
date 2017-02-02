from bs4 import BeautifulSoup
from pymongo import MongoClient
import requests
import sys

client = MongoClient()
db = client.rastreiobot

def check_package(code):
    cursor = db.rastreiobot.find_one({"code": code.upper()})
    if cursor:
        return True
    return False

def check_user(code, user):
    cursor = db.rastreiobot.find_one(
    {
            "code": code.upper(),
            "users": user
    })
    if cursor:
        return True
    return False

def add_package(code, user):
    stat = get_update(code)
    if stat == 0:
        stat = 'Sistema dos Correios fora do ar.'
    elif stat == 1:
        stat = None
    else:
        cursor = db.rastreiobot.insert_one (
        {
            "code" : code.upper(),
            "users" : [user],
            "stat" : stat
        })
        stat = 10
    return stat

def add_user(code, user):
    cursor = db.rastreiobot.update_one (
    { "code" : code.upper() },
    {
        "$push": {
            "users" : user
        }
    })

def set_desc(code, user, desc = None):
    if not desc:
        desc = code
    cursor = db.rastreiobot.update_one (
    { "code" : code.upper() },
    {
        "$set": {
            user : desc
        }
    })

def get_update(code):
    stats = []
    request = requests.Session()
    request.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'
    try:
        URL = ('http://websro.correios.com.br/sro_bin/txect01$.QueryList'
            +'?P_ITEMCODE=&P_LINGUA=001&P_TESTE=&P_TIPO=001&P_COD_UNI=')
        response = request.get(URL + code)
    except:
        print('Correios fora do ar')
        return 0
    html = BeautifulSoup(response.content, 'html.parser')
    tabela = html.findAll('tr')
    if len(tabela) < 1:
        print('Codigo não encontrado')
        return 1
    stats.append(str(u'\U0001F4EE') + ' <b>' + code + '</b>')
    for index in reversed(range(len(tabela))):
        # print(index)
        linhas = tabela[index].findAll('td')
        data = linhas[0]
        # print(data)
        if ':' not in data.text:
            continue
        try:
            local = linhas[1]
            situacao = linhas[2]
        except:
            observacao = data
            data = False
            situacao = False
        try:
            rowspan = int(linhas[0].get('rowspan'))
        except:
            rowspan = 1
        if int(rowspan) > 1:
            observacao = tabela[index+1].findAll('td')[0]
            index = index + 1
        else:
            observacao = False
        if data:
            mensagem = 'Data: ' + data.text
            if local:
                mensagem = mensagem + '\nLocal: ' + local.text
            if situacao:
                mensagem = (mensagem + '\nSituação: <b>' +
                    situacao.text + '</b>')
                if situacao.text == 'Entrega Efetuada':
                    mensagem = mensagem + ' ' + str(u'\U0001F381')
                elif situacao.text == 'Postado':
                    mensagem = mensagem + ' ' + str(u'\U0001F4E6')
            if observacao:
                mensagem = mensagem + '\nObservação: ' + observacao.text
        stats.append(mensagem)
    for elem in stats:
        print(elem)
        print('-')
    return stats

if __name__ == '__main__':
    code = sys.argv[1]
    user = '9083398'
    try:
        desc = sys.argv[2]
    except:
        pass
    # cursor = db.rastreiobot.delete_many({"code": "DV530695574BR"})
    # print('Deletados: ' + str(cursor.deleted_count))
    cursor = db.rastreiobot.find()
    exists = check_package(code)
    if exists:
        exists = check_user(code, user)
        if exists:
            pass
        else:
            print('Novo user')
            add_user(code, user)
    else:
        # print('Novo')
        stat = add_package(code, user)
        if stat == 0:
            print('Correios fora do ar')
        elif stat == 1:
            print('Pacote não encontrado')
        elif stat == 10:
            print('Pacote adicionado/atualizado')


    set_desc(code, user, desc)
    for elem in cursor:
        # print(elem)
        print('Codigo: ' + elem['code'])
        for user in elem['users']:
            print('Usuário: ' + user + ' Descrição: ' + elem[user])
        print('Último: ' + elem['stat'][len(elem['stat'])-1])
        print('\n')
