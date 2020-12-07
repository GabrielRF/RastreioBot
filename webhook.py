import asyncio
import configparser
import flask
import json
import sqlite3
import requests
from flask import abort, request
from db import User

config = configparser.ConfigParser()
config.sections()
BOT_CONFIG_FILE = 'bot.conf'
config.read(BOT_CONFIG_FILE)
db = config['SQLITE3']['data_base']
table = config['SQLITE3']['table']

webhook_host = config['WEBHOOK']['HOST']
webhook_port = config['WEBHOOK']['PORT']
webhook_key = config['WEBHOOK']['KEY']

meli_client_id = config['MERCADOLIVRE']['client_id']
meli_client_secret_key = config['MERCADOLIVRE']['secret_key']
meli_client_redirect_url = config['MERCADOLIVRE']['redirect_url']


app = flask.Flask(__name__)

def adduser(chatid='', picpayid='', sub_id=''):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    aux = ('''INSERT INTO {} (chatid, picpayid, sub_id)
        VALUES ('{}', '{}', '{}')''').format(table, chatid, picpayid, sub_id)
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
            adduser('', jsonData['event']['subscriber']['username'].lower(), jsonData['event']['subscriber']['id'])
    if jsonData['event_type'] == 'subscription_cancelled':
            deluser('sub_id', jsonData['event']['subscriber_id'])
    return "Hello"


@app.route("/meli/signup")
def meli_signup():
    code = request.args.get("code")
    # Gambiarra para relacionar usuário do telegram a sua conta no meli
    telegram_id = request.args.get("state")

    if not telegram_id or not code:
        abort(400)

    url = "https://api.mercadolivre.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": meli_client_id,
        "client_secret": meli_client_secret_key,
        "code": code,
        "redirect_uri": meli_client_redirect_url,
    }
    response = requests.post(url, json=data).json()

    meli_access_token = response["access_token"]
    meli_refresh_token = response["refresh_token"]

    user = User.update(
        telegram_id,
        upsert=True,
        meli_access_token=meli_access_token,
        meli_refresh_token=meli_refresh_token,
    )

    # TODO: notify user


@app.route("/meli/notifications")
def meli_notifications():
    pass



if __name__ == '__main__':
    app.run(host=webhook_host, port=webhook_port)
