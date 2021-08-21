from unittest.mock import AsyncMock, Mock, patch

from aiogram.utils.exceptions import BotBlocked, BotKicked, UserDeactivated, RetryAfter

import pytest

from rastreio.workers.update_packages import (
    build_message,
    is_finished,
    group_packages,
    send_update_to_user,
    should_update,
)


@pytest.mark.parametrize("package, expected_return", (
    ({"finished": True}, True),
    ({"stat": [
        "Estado anterior",
        "Objeto entregue ao destinatário",
    ]}, True),
    ({"stat": ["qualquer outro estado"]}, False),
))
def test_is_finished(package, expected_return):
    assert is_finished(package) == expected_return


@pytest.mark.parametrize("randint, is_finished, expected_return", (
    (0, True, True),
    (0, False, True),
    (1, True, False),
    (1, False, True),
))
@patch("rastreio.workers.update_packages.random.randint")
@patch("rastreio.workers.update_packages.is_finished")
def test_should_update(mocked_is_finished_package, mocked_randint, randint, is_finished, expected_return):
    mocked_is_finished_package.return_value = is_finished
    mocked_randint.return_value = randint

    package = {}
    assert should_update(package) == expected_return


def test_build_message():
    package = {}
    user = "123456"
    code = "AB012345678CD"
    stats = ["latest-stat"]

    message = build_message(package, user, code, stats)
    assert message == (
        "\U0001F4EE <a href='https://t.me/rastreiobot?start=AB012345678CD'>AB012345678CD</a>\n"
        "\nlatest-stat\n"
    )


def test_build_message_user_alias():
    user = "123456"
    package = {
        user: "package alias",
    }
    code = "AB012345678CD"
    stats = ["latest-stat"]

    message = build_message(package, user, code, stats)
    assert message == (
        "\U0001F4EE <a href='https://t.me/rastreiobot?start=AB012345678CD'>AB012345678CD</a>\n"
        "<b>package alias</b>\n"
        "\nlatest-stat\n"
    )


def test_build_message_final_stat():
    package = {}
    user = "123456"
    code = "AB012345678CD"
    stats = ["objeto entregue"]

    message = build_message(package, user, code, stats)
    assert message == (
        "\U0001F4EE <a href='https://t.me/rastreiobot?start=AB012345678CD'>AB012345678CD</a>\n"
        "\nobjeto entregue\n"
        "\n\U0001F4B3 Me ajude a manter o projeto vivo!\n"
        "Envie /doar e veja as opções \U0001F4B5"
    )


@patch("rastreio.workers.update_packages.PATREON", ["123456"])
def test_build_message_final_stat_patreon_user():
    package = {}
    user = "123456"
    code = "AB012345678CD"
    stats = ["objeto entregue"]

    message = build_message(package, user, code, stats)
    assert message == (
        "\U0001F4EE <a href='https://t.me/rastreiobot?start=AB012345678CD'>AB012345678CD</a>\n"
        "\nobjeto entregue\n"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("exception", (BotBlocked, BotKicked, UserDeactivated))
@patch("rastreio.workers.update_packages.db_ops.remove_user_from_package")
@patch("rastreio.workers.update_packages.bot.send_message")
async def test_send_update_to_user_exception_remove_user(mocked_send_message, mocked_remove_user_from_package, exception):
    code = "AB012345678CD"
    user = "123456"
    message = "message"

    mocked_send_message.side_effect = exception("exception")

    assert not await send_update_to_user(code, user, message, Mock())

    mocked_send_message.assert_called_once()
    mocked_remove_user_from_package.assert_called_once_with(code, user)


@pytest.mark.asyncio
@patch("rastreio.workers.update_packages.bot.send_message")
async def test_send_update_to_user_exception_remove_user(mocked_send_message):
    code = "AB012345678CD"
    user = "123456"
    message = "message"

    mocked_send_message.side_effect = Exception("unexpected exception")

    assert not await send_update_to_user(code, user, message, Mock())
    mocked_send_message.assert_called_once()


@pytest.mark.asyncio
@patch("rastreio.workers.update_packages.asyncio.sleep", AsyncMock())
@patch("rastreio.workers.update_packages.bot.send_message")
async def test_send_update_to_user_retry(mocked_send_message):
    code = "AB012345678CD"
    user = "123456"
    message = "message"

    mocked_send_message.side_effect = [RetryAfter("exception"), True]

    assert await send_update_to_user(code, user, message, Mock())
    assert mocked_send_message.call_count == 2


def test_group_packages():
    packages = range(20)
    batches = group_packages(packages, 3)
    assert len(batches) == 7
    assert len(batches[-1]) == 2
