from bottery.views import pong
from bottery.message import render


# Temporary fake database
pacotes_db = {}


def info(message):
    return render(message, 'info.md')


def add_pacote(message):
    pacote = message.text
    if pacotes_db.get(pacote):
        return pacotes_db[pacote]

    pacotes_db[pacote] = 'Aguardando verificação'
    return 'Pacote cadastrado.'


def lista_pacotes(message):
    return render(message, 'lista.md', {'pacotes': pacotes_db})


def pacotes_concluidos(message):
    pacotes = {pacote: status for pacote in pacotes_db if pacotes_db[pacote] == 'concluido'}
    return render(message, 'concluidos.md', {'pacotes': pacotes})

def deleta_pacote(message):
    pacote = message.text.split()[1]
    if pacotes_db.get(pacote):
        del pacotes_db[pacote]
    return 'Pacote removido'
