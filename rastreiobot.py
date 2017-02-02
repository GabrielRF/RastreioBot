from bs4 import BeautifulSoup
from check_update import check_update
from time import time
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
            "stat" : stat,
            "time" : str(time())
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
    return check_update(code)

if __name__ == '__main__':
    code = sys.argv[1].upper()
    user = '9083398'
    try:
        desc = sys.argv[2]
    except:
        desc = None
    # cursor = db.rastreiobot.delete_many({"code": sys.argv[1]})
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
        time_dif = int(time() - float(elem['time']))
        # print(time_dif)
        # print(elem)
        print('Codigo: \t' + elem['code'])
        for user in elem['users']:
            print('Usuário:\t' + user + ' Descrição: ' + elem[user])
        print('Verificado:\t' + elem['time'])
        print('Último estado: \t' + elem['stat'][len(elem['stat'])-1])
        print('\n')
