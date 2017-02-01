from pymongo import MongoClient
import sys

client = MongoClient()
db = client.rastreiobot

def check_package(code):
    cursor = db.rastreiobot.find_one({"code": code.upper()})
    # print(cursor)
    if cursor:
        return True
    return False

def check_user(code, user):
    cursor = db.rastreiobot.find_one(
    {
            "code": code.upper(),
            "user": user
    })
    if cursor:
        return True
    return False

def add_package(code, user):
    cursor = db.rastreiobot.insert_one (
    {
        "code" : code.upper(),
        "user" : [user],
        "stat" : None
    })
    # print(cursor.inserted_id)

def add_user(code, user):
    cursor = db.rastreiobot.update_one (
    { "code" : code.upper() }, 
    {
        "$push": { 
            "user" : user 
        }
    })

def get_update(code, rounds):
    request = requests.Session()
    request.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'
    try:
        response = request.get(URL + codigo)
    except:
        print('Correios fora do ar')
        return False
    html = BeautifulSoup(response.content, 'html.parser')
    tabela = html.findAll('tr')
    if len(tabela) < 1:
        print('Codigo não encontrado')
        return 0
    mensagem = str(u'\U0001F4EE') + ' <b>' + codigo + '</b>\n\n'
    for index in reversed(range(len(tabela))):
        if index > 0:
            # print(index)
            linhas = tabela[index].findAll('td')
            data = linhas[0]
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
                if int(rounds) > 0:
                    mensagem = str(u'\U0001F4EE') + ' <b>' + codigo + '</b>\nData: ' + data.text
                else:
                    mensagem = mensagem + 'Data: ' + data.text
                if local:
                    mensagem = mensagem + '\nLocal: ' + local.text
                if situacao:
                    mensagem = mensagem + '\nSituação: <b>' + situacao.text + '</b>'
                    if situacao.text == 'Entrega Efetuada':
                        mensagem = mensagem + ' ' + str(u'\U0001F381')
                    elif situacao.text == 'Postado':
                        mensagem = mensagem + ' ' + str(u'\U0001F4E6')
                if observacao:
                    mensagem = mensagem + '\nObservação: ' + observacao.text
                mensagem = mensagem + '\n\n'
    print(mensagem)

if __name__ == '__main__':
    code = sys.argv[1]
    user = '9083328'
    # cursor = db.rastreiobot.delete_many({"code": "DV530695574BR"})
    # print(cursor.deleted_count)
    cursor = db.rastreiobot.find()
    for elem in cursor:
        print(elem)
    exists = check_package(code)
    print(exists)
    if exists:
        print('Existe')
        exists = check_user(code, user)
        if exists:
            print('Existe')
        else:
            print('Novo user')
            add_user(code, user)
    else:
        print('Novo')
        add_package(code, user)
