import configparser
import logging.handlers
import sys
from datetime import datetime
from time import time, sleep
from utils import status
from utils import anuncieaqui
from utils.misc import check_update
from utils.misc import async_check_update
from utils.misc import check_type
import apis.apicorreios as correios
import apis.apitrackingmore as trackingmore
from rastreio import db as db_ops
from rastreio.progressbar import ProgressBar

import random
import requests

import asyncio
import motor.motor_asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils import executor
from aiogram.utils.exceptions import BotBlocked, BotKicked, UserDeactivated, RetryAfter
from aiogram.utils.markdown import quote_html


config = configparser.ConfigParser()
config.read("bot.conf")


TOKEN = config["RASTREIOBOT"]["TOKEN"]
RETRY_COUNT = int(config["RASTREIOBOT"]["retry_count"])
SEMAPHORE_SIZE = int(config["RASTREIOBOT"]["semaphore_size"])
LOG_ALERTS_FILE = config["RASTREIOBOT"]["alerts_log"]
PATREON = config["RASTREIOBOT"]["patreon"]
BATCH_SIZE = int(config["RASTREIOBOT"]["batch_size"])

logger = logging.getLogger("InfoLogger")
handler_info = logging.handlers.TimedRotatingFileHandler(
    LOG_ALERTS_FILE, when="midnight", interval=1, backupCount=7, encoding="utf-8"
)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler_info)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
client = motor.motor_asyncio.AsyncIOMotorClient()
db = client.rastreiobot


def is_finished(package):
    """Check if a package reached its final state"""
    if package.get("finished"):
        return True

    old_state = package["stat"][-1].lower()
    finished_states = [
        "objeto entregue ao",
        "objeto apreendido por órgão de fiscalização",
        "objeto devolvido",
        "objeto roubado",
        "delivered",
        "postado",
        "ect",
    ]

    for state in finished_states:
        if state in old_state:
            return True

    return False


def should_update(package):
    # Correios sometimes can incorrecly mark a packages as finished, and
    # update its status with the correct one. To catch thoses errors,
    # RastreioBot tries to update a % of the finalized packages.
    should_retry = random.randint(0, RETRY_COUNT)
    return not should_retry or not is_finished(package)


def build_message(package, user, code, stats):
    message = f"\U0001F4EE <a href='https://t.me/rastreiobot?start={code}'>{code}</a>\n"
    alias = package.get(user)
    if alias and alias != code:
        message += f"<b>{quote_html(alias)}</b>\n"

    message += f"\n{stats[-1]}\n"

    return message


async def send_update_to_user(code, user, message, progress, retry=3):
    try:
        try:
            await anuncieaqui.async_send_message(
                TOKEN, user, message
            )
        except:
            await bot.send_message(
                user, message, parse_mode="HTML", disable_web_page_preview=True
            )
    except (BotBlocked, BotKicked, UserDeactivated) as e:
        progress.print(
            f"{code}: exception while sending update to user. user={user}, exception={e.__class__}"
        )
        db_ops.remove_user_from_package(code, user)
        return False
    except RetryAfter as e:
        progress.print(f"{code}: Telegram flood control. user={user}")
        if retry > 0:
            progress.print(f"{code}: Retrying send message to user in 30s")
            await asyncio.sleep(30)
            return await send_update_to_user(code, user, message, progress, retry - 1)
        else:
            return False
    except Exception as e:
        progress.print(
            f"{code}: exception while sending update to user. user={user}, exception={e.__class__}"
        )
        return False

    logger.info(f"{datetime.now()} Update sent to user. code={code}, user={user}")
    return True


async def check_and_update(code, number_of_updates, after, progress):
    if number_of_updates >= len(after):
        # We can't just check if the number of updates is different because
        # from time to time, Correios can remove updates from old packages
        # history.
        progress.advance()
        # TODO raise exception?
        return

    query_result = await db.rastreiobot.update_one(
        {"code": code},
        {"$set": {"stat": after}},
    )
    progress.print(f"{code}: update stored on database")

    package = await db.rastreiobot.find_one(
        {"code": code},
        {"stat": 0},
    )

    users = package.get("users", [])
    for user in users:
        message = build_message(package, user, code, after)

        await send_update_to_user(code, user, message, progress, retry=3)
        progress.print(f"{code}: update sent to user. user={user}")

    progress.advance()


async def update_package_group(packages, semaphore, progress):
    async with semaphore:
        codes = [package["code"] for package in packages]
        updates = await async_check_update(codes, 1)
        if updates in [status.OFFLINE, status.NOT_FOUND, status.NOT_FOUND_TM]:
            progress.print(f"No updates returned by Correios. updates={updates!r}")
            progress.advance(len(packages))
            return None

        if not isinstance(updates, dict):
            # When async_check_update fails, it returns integers as status codes. So we
            # need to confirm the updates are actually dictionaries before using it.
            progress.advance(len(packages))
            progress.print(f"No updates returned by Correios. updates={updates!r}")
            return None

        tasks = []
        for package in packages:
            code = package["code"]
            number_of_updates = package["number_of_updates"]
            after = updates[code]

            if not after:
                continue

            tasks.append(check_and_update(code, number_of_updates, after, progress))

        packages_without_update = len(packages) - len(tasks)
        progress.advance(packages_without_update)

        await asyncio.gather(*tasks)


async def get_packages_to_update():
    pipeline = [
        {
            "$project": {
                "code": True,
                "finished": True,
                "stat": {"$slice": ["$stat", -1]},
                "number_of_updates": {"$size": "$stat"},
            }
        }
    ]
    return await db.rastreiobot.aggregate(pipeline).to_list(length=None)


def group_packages(packages, batch_size):
    return [packages[i : i + batch_size] for i in range(0, len(packages), batch_size)]


async def main():
    packages = await get_packages_to_update()
    print(f"Total packages: {len(packages)}")

    packages = list(filter(lambda p: should_update(p), packages))
    packages = list(filter(lambda p: check_type(p["code"]) is correios, packages))

    batches = group_packages(packages, BATCH_SIZE)
    print(f"Number of batches: {len(batches)}, batch_size={BATCH_SIZE}")

    with ProgressBar("Packages", total=len(packages)) as progress:
        semaphore = asyncio.BoundedSemaphore(SEMAPHORE_SIZE)
        tasks = [update_package_group(batch, semaphore, progress) for batch in batches]
        await asyncio.gather(*tasks)


def run():
    executor.start(dp, main())


if __name__ == "__main__":
    run()
