import configparser
import status
import trackingmore
import sys
from datetime import datetime

import apigeartrack as geartrack

# https://www.trackingmore.com/api-index.html
config = configparser.ConfigParser()
config.sections()
config.read('bot.conf')

key = config['TRACKINGMORE']['key']
trackingmore.set_api_key(key)


def get_or_create_tracking_item(carrier, code):
    try:
        tracking_data = trackingmore.create_tracking_data(carrier, code)
        trackingmore.create_tracking_item(tracking_data)
        tracking_data = trackingmore.get_tracking_item(carrier, code)
    except trackingmore.trackingmore.TrackingMoreAPIException as e:
        if e.err_code == 4016: # Already exists
            tracking_data = trackingmore.get_tracking_item(carrier, code)
        else:
            raise e

    return tracking_data


def get_carriers(code):
    carriers = trackingmore.detect_carrier_from_code(code)
    carriers.sort(key=lambda carrier: carrier['code'])
    return carriers


def get(code, *args, **kwargs):
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
            print(carrier, tracking_data)
            if not tracking_data or 'status' not in tracking_data:
                response_status = status.OFFLINE
            elif tracking_data['status'] == 'notfound':
                response_status = status.NOT_FOUND_TM
            elif len(tracking_data) >= 10:
                return formato_obj(tracking_data, carrier, code)

    return response_status


def formato_obj(json, carrier, code):
    stats = []
    stats.append(str(u'\U0001F4EE') + ' <b>' + json['tracking_number'] + '</b>')
    tabela = json['origin_info']['trackinfo']
    mensagem = ''
    for evento in reversed(tabela):
        data = evento['Date'].strftime("%d/%m/%Y %H:%M")
        situacao = evento['StatusDescription']
        observacao = evento['checkpoint_status']
        if 'Import clearance success' in situacao:
            try:
                observacao = '<code>' + geartrack.getcorreioscode(carrier, code) + '</code>'
            except:
                pass
        mensagem = ('Data: {}' +
            '\nSituacao: <b>{}</b>' +
            '\nObservação: {}'
        ).format(data, situacao, observacao)
        stats.append(mensagem)
    return stats


if __name__ == '__main__':
    print(get(sys.argv[1], 0))
    #get(sys.argv[1], 0)
