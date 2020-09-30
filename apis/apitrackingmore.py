import configparser
import sys
import apis.apicorreios as correios
from datetime import datetime

import trackingmore
from pymongo import MongoClient

import apis.apigeartrack as geartrack
import db
from utils import status

# https://www.trackingmore.com/api-index.html - Codigos de retorno da API
config = configparser.ConfigParser()
config.read('bot.conf')

key = config['TRACKINGMORE']['key']
trackingmore.set_api_key(key)


def get_or_create_tracking_item(carrier, code):
    print(carrier)
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
    cursor = db.search_package(code)
    try:
        if type(cursor['carrier']) is dict:
            return [cursor['carrier']]
        return cursor['carrier']
    except:
        try:
            carriers = trackingmore.detect_carrier_from_code(code)
        except Exception as e:
            print(e)
            raise IndexError
        carriers.sort(key=lambda carrier: carrier['code'])
        db.update_package(code, carrier=carriers)
    return carriers

def get(code, retries=0):
    try:
        carriers = get_carriers(code)
    except IndexError:
        return status.TYPO
    except trackingmore.trackingmore.TrackingMoreAPIException as e:
        return status.NOT_FOUND_TM

    response_status = status.NOT_FOUND_TM
    for carrier in carriers:
        try:
            if carrier['code'] == 'correios':
                codigo_novo = db.search_package(code)["code_br"]
                return correios.get(codigo_novo, 3)
        except TypeError:
            pass
        try:
            tracking_data = get_or_create_tracking_item(carrier['code'], code)
            print(tracking_data)
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
                print(tracking_data)
            #elif len(tracking_data) >= 10:
            elif tracking_data['status'] == 'transit':
                db.update_package(code, carrier=carrier)
                return formato_obj(tracking_data, carrier, code, retries)
            elif tracking_data['status'] == 'expired':
                db.update_package(code, carrier=carrier)
                return formato_obj(tracking_data, carrier, code, retries)
            elif tracking_data['status'] == 'delivered':
                db.update_package(code, carrier=carrier)
            elif tracking_data['status'] == 'pickup':
                db.update_package(code, carrier=carrier)
                return formato_obj(tracking_data, carrier, code, retries)

    return response_status


def formato_obj(json, carrier, code, retries):
    stats = []
    stats.append(str(u'\U0001F4EE') + ' <b>' + json['tracking_number'] + '</b>')
    try:
        tabela = json['origin_info']['trackinfo']
    except KeyError:
        if retries > 0:
            return get(code, retries-1)
        else:
            return status.NOT_FOUND_TM
    for evento in reversed(tabela):
        codigo_novo = None
        print(code)
        print(evento['Date'])
        # try:
        #     data = datetime.strptime(evento['Date'], '%Y-%m-%d %H:%M:%S').strftime("%d/%m/%Y %H:%M")
        # except ValueError:
        #     data = datetime.strptime(evento['Date'], '%Y-%m-%d %H:%M').strftime("%d/%m/%Y %H:%M")
        data = evento['Date']
        situacao = evento['StatusDescription']
        observacao = evento['checkpoint_status']
        try:
            codigo_novo = geartrack.getcorreioscode(carrier['code'], code)
            if codigo_novo:
                carrier = {'code': 'correios', 'name': 'Correios'}
                db.update_package(code, carrier=carrier, code_br=codigo_novo)
                return correios.get(codigo_novo, 3)
        except:
            pass
        mensagem = ('Data: {}'
            '\nSituacao: <b>{}</b>'
            '\nObservação: {}'
        ).format(data, situacao, observacao)
        stats.append(mensagem)
    return stats

if __name__ == '__main__':
    print(get(sys.argv[1], retries=3))
