from check_update import check_update
from pymongo import MongoClient
from time import time
import sys

client = MongoClient()
db = client.rastreiobot

def get_package(code, user):
    stat = check_update(code)
    if stat == 0:
        stat = 'Sistema dos Correios fora do ar.'
    elif stat == 1:
        stat = None
    else:
        cursor = db.rastreiobot.update_one (
        { "code" : code.upper() },
        {
            "$set": {
                "stat" : stat,
                "time" : str(time())
            }
        })
        stat = 10
    return stat

if __name__ == '__main__':
    code = sys.argv[1]
    user = '9083329'
    cursor = db.rastreiobot.find()
    for elem in cursor:
        time_dif = int(time() - float(elem['time']))
        print(time_dif)
        if time_dif > 10:
            get_package(elem['code'], user)
        # print(elem)
        print('Codigo: \t' + elem['code'])
        for user in elem['users']:
            print('Usuário:\t' + user + ' Descrição: ' + elem[user])
        print('Verificado:\t' + elem['time'])
        print('Último estado: \t' + elem['stat'][len(elem['stat'])-1])
        print('\n')
