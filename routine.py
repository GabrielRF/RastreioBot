from check_update import check_update
from pymongo import MongoClient
from time import time, sleep
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
    while True:
        cursor1 = db.rastreiobot.find()
        for elem in cursor1:
            code = elem['code']
            old_state = elem['stat'][len(elem['stat'])-1]
            if 'Entrega Efetuada' in old_state:
                continue
            print(code)
            # print('Old: ' + old_state)
            cursor2 = db.rastreiobot.find_one(
            {
                "code": code
            })
            new_state = cursor2['stat'][len(elem['stat'])-1]
            # print('New: ' + new_state)
            users = elem['users']
            if old_state != new_state:
                print('Novidade')
                for user in users:
                    print(user)
            else:
                print('Igual')
            sleep(3)
        print('---')
        sleep(60)
