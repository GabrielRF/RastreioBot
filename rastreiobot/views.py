from bottery.views import pong
from bottery.message import render


# Temporary fake database
pacotes_db = {}


def info(message):
    return render(message, 'info.md')


def add_pacote(message):
    pacote = message.text
    if pacotes_db.get(pacote):
        return pacotes_db[pacote]['status']

    pacotes_db[pacote] = {
        'status': 'Aguardando verificação',
    }
    return 'Pacote cadastrado.'


def lista_pacotes(message):
    return render(message, 'lista.md', {'pacotes': pacotes_db})
