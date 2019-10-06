import re

CORREIO_PATTERN = re.compile(r"^[A-Za-z]{2}\d{9}[A-Za-z]{2}$")
ALIEXPRESS_PATTERN = re.compile(
    r"^([A-Za-z]{2}\d{14}|[A-Za-z]{4}\d{9}|\d{10}|[A-Za-z]{5}\d{10}[A-Za-z]{2})$"
)

def get_carrier_by_code(code):
    if CORREIO_PATTERN.search(code):
        from carriers import correios
        return correios

    if ALIEXPRESS_PATTERN.search(code):
        from carriers import trackingmore
        return trackingmore

    return None
