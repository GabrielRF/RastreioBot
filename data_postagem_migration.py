'''
Migração para criar uma nova key no banco de pacotes.
A nova key contém a data de postagem dos correios, que vai ser utilizada para ordenar os pacotes

Para aplicar a migração basta rodar:
    $ python data_postagem_migration.py
'''


from pymongo import MongoClient
import re
from datetime import datetime

client = MongoClient()
db = client.rastreiobot


def get_data_postagem(stat):
    '''
    Recupera a data de postagem a partir dos status do pacote

    Args:
        stat (list): lista de status

    Returns:
        string: data de postagem 
    '''
    for mensagem in stat:
        if 'postado' in mensagem:
            data_regex = re.compile(r'Data: ([\d]{2}\/[\d]{2}\/[\d]{4} [\d]{2}\:[\d]{2})')
            try:
                data_postagem = data_regex.match(mensagem).group(1)
            except AttributeError:
                data_postagem = ''
            return data_postagem


def migrate():
    '''
    Realiza a migração dos dados

    A migração recupera a data de postagem do status e cria uma nova key com o valor da data

    Returns:
        int: quantidade de pacotes atualizados
    '''
    print('Iniciando migração')
    todos_pacotes = list(db.rastreiobot.find({'data_postagem': {'$exists': False}}))
    count = 1
    pacotes_migrados = 0
    for pacote in todos_pacotes:
        print('Migrando pacote %d de %d' % (count, len(todos_pacotes)))
        count += 1

        pacote_stats = pacote.get('stat', [])
        data_postagem_str = get_data_postagem(pacote_stats)
        if data_postagem_str:
            # cria um datetime a partir da data extraída do status
            data_postagem = datetime.strptime(data_postagem_str, '%d/%m/%Y %H:%M')
            # atualiza pacote com a data de postagem dos correios
            db.rastreiobot.update_one({'_id': pacote['_id']}, {'$set': {'data_postagem': data_postagem}})
            pacotes_migrados += 1
    return pacotes_migrados


if __name__ == '__main__':
    pacotes_migrados = migrate()
    print('Migração finalizada!')
    print('%d pacotes atualizados.' % pacotes_migrados)