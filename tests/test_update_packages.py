import pytest

from rastreio.workers.update_packages import is_finished_package


@pytest.mark.parametrize("package, expected_return", (
    ({"finished": True}, True),
    ({"stat": [
        "Estado anterior",
        "Objeto entregue ao destinatário",
    ]}, True),
    ({"stat": ["qualquer outro estado"]}, False),
))
def test_is_finished_package(package, expected_return):
    assert is_finished_package(package) == expected_return
