import pytest

from rastreiobot import package_status_can_change, count_packages


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


@pytest.fixture
def all_packages():
    packages = [
        {
            'code': 'PN123456789BR',
            'users': ['154120594'],
            'stat': ['📮 <b>PN123456789BR</b>', 'Aguardando recebimento pela ECT.'],
            'time': 1602997062.541877,
            '154120594': 'Minha encomenda'
        },
        {
            'code': 'PN123456791BR',
            'users': ['154120594'],
            'stat': ['📮 <b>PN123456791BR</b>', 'Objeto roubado.'],
            'time': 1602997062.541877,
            '154120594': 'Minha encomenda 2'
        }
    ]
    return packages


def test_count_packages(mocker, all_packages):
    mocked = mocker.patch('rastreio.db.PackagesRepository.all_packages')
    mocked.return_value = all_packages

    assert dict(count_packages()) == {
        'qtd': 1,
        'wait': 1,
        'extraviado': 1,
        }
