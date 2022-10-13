import json
from unittest.mock import Mock, call, patch

from apis.apicorreios import (
    parse,
    parse_multiple_codes_output,
    parse_single_code_output,
)



@patch("apis.apicorreios.parse")
def test_parse_single_code_output(mocked_parse):
    stats = ["stats"]
    mocked_parse.return_value = stats

    code = "AB012345678BR"
    events = []
    response = {
        "objeto": [{
            "evento": events,
            "numero": code,
        }],
    }

    assert parse_single_code_output(response) == stats
    mocked_parse.assert_called_once_with(code, events)


@patch("apis.apicorreios.parse")
def test_parse_multiple_codes_output(mocked_parse):
    stats1 = ["stats1"]
    stats2 = ["stats2"]
    mocked_parse.side_effect = [stats1, stats2]

    code1 = "AB012345678BR"
    code2 = "CD012345678BR"
    events1 = events2 = []

    response = {
        "objeto": [{
            "evento": events1,
            "numero": code1,
        }, {
            "evento": events2,
            "numero": code2,
        }],
    }

    assert parse_multiple_codes_output(response) == {
        code1: stats1,
        code2: stats2,
    }

    mocked_parse.assert_has_calls([
        call(code1, events1),
        call(code2, events2),
    ])


@patch("apis.apicorreios.db.PackagesRepository.update_package")
def test_parse_package_in_transit(mocked_update_package):
    with open("tests/data/correios-package-in-transit.json") as file:
        returned_package = json.load(file)

    code = returned_package["objeto"][0]["numero"]
    events = returned_package["objeto"][0]["evento"]

    events = parse(code, events)

    assert len(events) == 3
    assert '📮<a href="https://t.me/rastreiobot?start=AB019345678BR">AB019345678BR</a>' == events[0]
    assert (
        "Data: 10/03/2020 14:01\n"
        "Local: Agf Cruzeiro Sao Paulo\n"
        "Situação: <b>Objeto postado</b> 📦"
    ) == events[1]

    assert (
        "Data: 10/03/2020 14:17\n"
        "Local: Agf Cruzeiro Sao Paulo\n"
        "Situação: <b>Objeto em trânsito - por favor aguarde</b>\n"
        "Observação: Cte Sao Paulo"
    ) == events[2]
    assert not mocked_update_package.called
