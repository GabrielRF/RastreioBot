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
        print('1: ' + str(response))
#         if '200' not in str(response):
#             print('Correios fora do ar')
#             if '200' not in str(response):
#                 URL = ('http://sro.micropost.com.br/consulta.php?objetos=')
#                 response = request.get(URL + code)
#                 print('2: ' + str(response))
    except:
        return 0
    if '200' not in str(response):
        return 0
    print(len(str(response)))
    if len(str(response)) < 10:
        print('aaaaaaa')
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
            mensagem = 'Data: ' + data.text.strip()
            if local:
                mensagem = mensagem + '\nLocal: ' + local.text.strip()
            if situacao:
                mensagem = (mensagem + '\nSituação: <b>' +
                    situacao.text.strip() + '</b>')
                if situacao.text == 'Entrega Efetuada':
                    mensagem = mensagem + ' ' + str(u'\U0001F381')
                elif situacao.text == 'Postado':
                    mensagem = mensagem + ' ' + str(u'\U0001F4E6')
            if observacao:
                mensagem = mensagem + '\nObservação: ' + observacao.text.strip()
                if 'Liberado sem' in observacao.text:
                    mensagem = mensagem + ' ' + str(u'\U0001F389')
        stats.append(mensagem)
    # for elem in stats:
        # print(elem)
        # print('-')
    return stats
