import status
from misc import check_type
import apicorreios as correios
import apitrackingmore as trackingmore

def check_update(code, max_retries=3):
    api_type = check_type(code)
    if api_type is not (correios or trackingmore):
        return status.TYPO
    try:
        return api_type.get(code, max_retries)
    except Exception:
        if api_type is correios:
            return status.NOT_FOUND
        elif api_type is trackingmore:
            return status.NOT_FOUND_TM
