import configparser
import status
import trackingmore
import sys
from datetime import datetime
from pymongo import ASCENDING, MongoClient

import apigeartrack as geartrack

# https://www.trackingmore.com/api-index.html - Codigos de retorno da API
config = configparser.ConfigParser()
config.sections()
config.read('bot.conf')

key = config['TRACKINGMORE']['key']
trackingmore.set_api_key(key)

client = MongoClient()
db = client.rastreiobot

def set_carrier_db(code, carrier):
    db.rastreiobot.update_one({
        "code": code.upper()}, {
        "$set": {
            "carrier": carrier
        }
    })


def get_or_create_tracking_item(carrier, code):

    try:
        tracking_data = trackingmore.get_tracking_item(carrier, code)
    except trackingmore.trackingmore.TrackingMoreAPIException as e:
        if e.err_code == 4031 or e.err_code == 4017:
            tracking_data = trackingmore.create_tracking_data(carrier, code)
            trackingmore.create_tracking_item(tracking_data)
            tracking_data = trackingmore.get_tracking_item(carrier, code)
        else:
            raise e

    return tracking_data


def get_carriers(code):
    package = db.rastreiobot.find_one({
        "code": code
    })
    
    if package:
        carriers = package['carrier']
        return carriers if isinstance(carriers, list) else [carriers]

    carriers = trackingmore.detect_carrier_from_code(code)
    carriers.sort(key=lambda carrier: carrier['code'])
    set_carrier_db(code, carriers)
    return carriers


def get(code, retries=0):
    try:
        carriers = get_carriers(code)
    except trackingmore.trackingmore.TrackingMoreAPIException as e:
        return status.NOT_FOUND_TM

    response_status = status.NOT_FOUND
    for carrier in carriers:
        try:
            tracking_data = get_or_create_tracking_item(carrier['code'], code)
        except trackingmore.trackingmore.TrackingMoreAPIException as e:
            if e.err_code == 4019 or e.err_code == 4021:
                response_status = status.OFFLINE
            elif e.err_code == 4031:
                response_status = status.NOT_FOUND_TM
        else:
            if not tracking_data or 'status' not in tracking_data:
                response_status = status.OFFLINE
            elif tracking_data['status'] == 'notfound':
                response_status = status.NOT_FOUND_TM
            elif len(tracking_data) >= 10:
                set_carrier_db(code, carrier)
                return formato_obj(tracking_data, carrier, code, retries)

    return response_status


def formato_obj(json, carrier, code, retries):
    stats = []
    stats.append(str(u'\U0001F4EE') + ' <b>' + json['tracking_number'] + '</b>')
    try:
        tabela = json['origin_info']['trackinfo']
    except KeyError:
        if retries < 0:
            return get(sys.argv[1], retries-1)
        else:
            return status.NOT_FOUND_TM
    mensagem = ''
    for evento in reversed(tabela):
        try:
            data = datetime.strptime(evento['Date'], '%Y-%m-%d %H:%M:%S').strftime("%d/%m/%Y %H:%M")
        except ValueError:
            data = datetime.strptime(evento['Date'], '%Y-%m-%d %H:%M').strftime("%d/%m/%Y %H:%M")
        situacao = evento['StatusDescription']
        observacao = evento['checkpoint_status']
        try:
            observacao = 'Código novo: <code>' + geartrack.getcorreioscode(carrier, code) + '</code>'
        except:
            pass
        mensagem = ('Data: {}' +
            '\nSituacao: <b>{}</b>' +
            '\nObservação: {}'
        ).format(data, situacao, observacao)
        stats.append(mensagem)
    return stats


if __name__ == '__main__':
    print(get(sys.argv[1], retries=3))
    #get(sys.argv[1], 0)
    #print(get_carriers(sys.argv[1]))
