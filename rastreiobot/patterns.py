import re

from bottery.conf.patterns import Pattern

from views import add_pacote, info, deleta_pacote, lista_pacotes, pacotes_concluidos


class StartswithPattern(Pattern):
    def check(self, message):
        if message.text.startswith(self.pattern):
            return self.view
        return False


class RegexPattern(Pattern):
    def check(self, message):
        if bool(re.match(self.pattern, message.text)):
            return self.view
        return False


patterns = [
    Pattern('/info', info),
    Pattern('/pacotes', lista_pacotes),
    Pattern('/concluidos', pacotes_concluidos),
    StartswithPattern('/del', deleta_pacote),
    RegexPattern(r'^[A-Za-z]{2}\d{9}[A-Za-z]{2}$', add_pacote),
]
