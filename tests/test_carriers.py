import pytest
from unittest import mock

from carriers import correios, get_carrier_by_code, trackingmore


@pytest.mark.parametrize("code,carrier", (
    ("AB123456789CD", correios),
    ("LP00147037652437", trackingmore),
    ("wrong-code", None),
))
def test_get_carrier_by_code(code, carrier):
    assert get_carrier_by_code(code) == carrier
