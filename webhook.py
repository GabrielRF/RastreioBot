import configparser
import flask
import json
import sqlite3
from flask import request

config = configparser.ConfigParser()
config.sections()
BOT_CONFIG_FILE = 'bot.conf'
config.read(BOT_CONFIG_FILE)
db = config['SQLITE3']['data_base']
table = config['SQLITE3']['table']

webhook_host = config['WEBHOOK']['HOST']
webhook_port = config['WEBHOOK']['PORT']
webhook_key = config['WEBHOOK']['KEY']

app = flask.Flask(__name__)

def adduser(chatid='', picpayid=''):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    aux = ('''INSERT INTO {} (chatid, picpayid)
        VALUES ('{}', '{}')''').format(table, chatid, picpayid)
    cursor.execute(aux)
    conn.commit()
    conn.close()

def deluser(arg1, arg1_value):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    aux = ('''DELETE FROM {}
        WHERE {} = {}''').format(table, arg1, arg1_value)
    cursor.execute(aux)
    conn.commit()
    conn.close()

def updateuser(arg1, arg1_value, arg2, arg2_value):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    aux = ('''UPDATE {} SET {} = "{}"
            WHERE {} = "{}"''').format(table, arg1, arg1_value, arg2, arg2_value)
    cursor.execute(aux)
    conn.commit()
    conn.close()

def select_user(col, arg):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    aux = ('''SELECT * FROM {} WHERE
       {} ="{}"''').format(table, col, arg)
    cursor.execute(aux)
    data = cursor.fetchone()
    conn.close()
    return data


#@app.route('/' + webhook_key + '/')
#def hello():
#    return ""

@app.route('/' + webhook_key + '/', methods=['POST'])
def secbox():
    jsonData = request.get_json()
    if webhook_key not in str(request.headers['X-Verification-Key']):
        return "Error"
    if jsonData['event_type'] == 'new_subscription':
        if not select_user('picpayid', jsonData['event']['subscriber']['username']):
            adduser('', jsonData['event']['subscriber']['username'].lower())
    if jsonData['event_type'] == 'subscription_cancelled':
            deluser('picpayid', jsonData['event']['subscriber']['username'].lower())
    return "Hello"

if __name__ == '__main__':
    app.run(host=webhook_host, port=webhook_port)

