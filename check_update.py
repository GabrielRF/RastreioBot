import requests
from bs4 import BeautifulSoup

def check_update(code):
    stats = []
    request = requests.Session()
    request.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36'
    try:
        URL = ('http://websro.correios.com.br/sro_bin/txect01$.QueryList'
            +'?P_ITEMCODE=&P_LINGUA=001&P_TESTE=&P_TIPO=001&P_COD_UNI=')
        response = request.get(URL + code)
    except:
        print('Correios fora do ar')
        return 0
    if '200' not in str(response):
        return 0
    html = BeautifulSoup(response.content, 'html.parser')
    tabela = html.findAll('tr')
    if len(tabela) < 1:
        print('Codigo não encontrado')
        return 1
    stats.append(str(u'\U0001F4EE') + ' <b>' + code + '</b>')
    for index in reversed(range(len(tabela))):
        # print(index)
        linhas = tabela[index].findAll('td')
        data = linhas[0]
        # print(data)
        if ':' not in data.text:
            continue
        try:
            local = linhas[1]
            situacao = linhas[2]
        except:
            observacao = data
            data = False
            situacao = False
        try:
            rowspan = int(linhas[0].get('rowspan'))
        except:
            rowspan = 1
        if int(rowspan) > 1:
            observacao = tabela[index+1].findAll('td')[0]
            index = index + 1
        else:
            observacao = False
        if data:
            mensagem = 'Data: ' + data.text
            if local:
                mensagem = mensagem + '\nLocal: ' + local.text
            if situacao:
                mensagem = (mensagem + '\nSituação: <b>' +
                    situacao.text + '</b>')
                if situacao.text == 'Entrega Efetuada':
                    mensagem = mensagem + ' ' + str(u'\U0001F381')
                elif situacao.text == 'Postado':
                    mensagem = mensagem + ' ' + str(u'\U0001F4E6')
                elif situacao.text == 'Liberado sem':
                    mensagem = mensagem + ' ' + str(u'\U0001F389')
            if observacao:
                mensagem = mensagem + '\nObservação: ' + observacao.text
        stats.append(mensagem)
    # for elem in stats:
        # print(elem)
        # print('-')
    return stats
