import configparser
import status
import trackingmore
import sys

import apigeartrack as geartrack

# https://www.trackingmore.com/api-index.html
config = configparser.ConfigParser()
config.sections()
config.read('bot.conf')

key = config['TRACKINGMORE']['key']
trackingmore.set_api_key(key)

carriers = ('cainiao', 'laos-post', 'dhl', 'sunyou')

def get(code, times):
    td = None
    for carrier in carriers:
        try:
            td = trackingmore.create_tracking_data(carrier, code)
            trackingmore.create_tracking_item(td)
            td = trackingmore.get_tracking_item(carrier, code)
        except trackingmore.trackingmore.TrackingMoreAPIException as e:
            if e.err_code == 4019 or e.err_code == 4021:
                return status.OFFLINE
            if e.err_code == 4016: # Already exists
                try:
                    td = trackingmore.get_tracking_item(carrier, code)
                except trackingmore.trackingmore.TrackingMoreAPIException as e:
                    if e.err_code == 4019 or e.err_code == 4021:
                        return status.OFFLINE
        if td is not None and td['status'] != 'notfound':
            break

    print(td)
    if td['status'] == 'notfound':
        return status.NOT_FOUND_TM
    elif len(td) < 10:
        return status.OFFLINE
    return formato_obj(td, carrier, code)


def formato_obj(json, carrier, code):
    stats = []
    stats.append(str(u'\U0001F4EE') + ' <b>' + json['tracking_number'] + '</b>')
    tabela = json['origin_info']['trackinfo']
    mensagem = ''
    for evento in reversed(tabela):
        data = evento['Date']
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
