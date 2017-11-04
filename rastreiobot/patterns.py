import re

from bottery.conf.patterns import Pattern

from views import add_pacote, info, lista_pacotes


class RegexPattern(Pattern):
    def check(self, message):
        if bool(re.match(self.pattern, message.text)):
            return self.view
        return False


patterns = [
    Pattern('/info', info),
    Pattern('/pacotes', lista_pacotes),
    RegexPattern(r'^[A-Za-z]{2}\d{9}[A-Za-z]{2}$', add_pacote),
]
