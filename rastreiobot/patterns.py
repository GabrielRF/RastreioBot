from bottery.conf.patterns import Pattern
from bottery.views import ping


patterns = [
    Pattern('ping', ping),
]
