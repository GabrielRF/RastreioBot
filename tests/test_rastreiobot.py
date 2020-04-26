import pytest

from rastreiobot import package_status_can_change


@pytest.mark.parametrize("package,expected_value", (
    ({"stat": ["Saída para entrega cancelada"]}, True),
    ({"stat": ["Objeto saiu para entrega ao destinatário"]}, True),
    ({"stat": ["Objeto devolvido ao país de origem"]}, True),
    ({"stat": ["Objeto entregue ao destinatário"]}, False),
    ({"stat": ["Objeto apreendido por órgão de fiscalização ou outro órgão anuente"]}, False),
    ({"stat": ["Delivered"]}, False),
    ({"stat": ["Objeto saiu para entrega", "Objeto roubado"]}, False),
))
def test_package_status_can_change(package, expected_value):
    assert package_status_can_change(package) == expected_value


