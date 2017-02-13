import configparser
import datetime
import sqlite3
import sys
import telebot
import sqlite3
from pymongo import MongoClient

def get_data():
    client = MongoClient()
    db = client.rastreiobot
    cursor = db.rastreiobot.find()
    not_finished = 0
    finished = 0
    users = []
    for elem in cursor:
        if 'Entrega Efetuada' not in elem['stat'][len(elem['stat'])-1]:
            not_finished = not_finished + 1
        else:
            time_dif = int(time() - float(elem['time']))
            if time_dif < 86400:
                finished = finished + 1
        for user in elem['users']:
            if user not in users:
                users.append(user)

    print('Em andamento: ' + str(not_finished))
    print('Finalizados: ' + str(finished))
    print('Usuários: ' + str(len(users)))
    data = str(datetime.datetime.now())
    return data, not_finished, finished, len(users)

if __name__ == '__main__':

    config = configparser.ConfigParser()
    config.sections()
    config.read('bot.conf')

    db = 'RastreioBot.db'
    table = 'RastreioBot'

    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    aux = ('''CREATE TABLE {} (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        data DATE NOT NULL,
        andamento TEXT NOT NULL,
        finalizados TEXT NOT NULL,
        usuarios TEXT NOT NULL);
    ''').format(table)

    aux2 = ('''SELECT * FROM "{}"''').format(table)
    try:
        cursor.execute(aux)
        print('Tabela criada. Nenhum valor inserido.')
        conn.commit()
        conn.close()
    except:
        select = cursor.execute(aux2)
        for line in select:
            print(line)
        conn.close()
        data, andamento, finalizados, usuarios = get_data()
        data = str(datetime.datetime.now())
        aux3 = ('''INSERT INTO 'RastreioBot' (data, andamento, finalizados, usuarios)
            VALUES ('{}', '{}', '{}', '{}')''').format(data, andamento, finalizados, usuarios)
        conn = sqlite3.connect(db) 
        cursor = conn.cursor()
        cursor.execute(aux3)
        conn.commit()
        conn.close()


