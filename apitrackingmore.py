import configparser
import status
import trackingmore
import sys

# https://www.trackingmore.com/api-index.html
config = configparser.ConfigParser()
config.sections()
config.read('bot.conf')

key = config['TRACKINGMORE']['key']
trackingmore.set_api_key(key)

def get(code, times):
    try:
        td = trackingmore.create_tracking_data('cainiao', code)
        trackingmore.create_tracking_item(td)
    except trackingmore.trackingmore.TrackingMoreAPIException as e:
        if e.err_code == 4016: # Already exists
            td = trackingmore.get_tracking_item('cainiao', code)
    print(td)
    if td['status'] == 'notfound':
        return status.NOT_FOUND_TM
    elif len(td) < 10:
        return status.OFFLINE
    return formato_obj(td)


def formato_obj(json):
    stats = []
    stats.append(str(u'\U0001F4EE') + ' <b>' + json['tracking_number'] + '</b>') 
    tabela = json['origin_info']['trackinfo']
    mensagem = ''
    for evento in reversed(tabela):
        data = evento['Date']
        situacao = evento['StatusDescription']
        observacao = evento['checkpoint_status']
        mensagem = ('Data: {}' +
            '\nSituacao: <b>{}</b>' +
            '\nObservação: {}'
        ).format(data, situacao, observacao)
        stats.append(mensagem)
    return stats
        

if __name__ == '__main__':
    print(get(sys.argv[1], 0))
    #get(sys.argv[1], 0)
