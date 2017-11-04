from bottery.conf.patterns import Pattern
from bottery.views import pong
from bottery.message import render


def info(message):
    return render(message, 'info.md')


patterns = [
    Pattern('ping', pong),
    Pattern('/info', info),
]
