import configparser
import logging.handlers
from datetime import datetime
from time import time

import telebot
from rich.progress import track

from rastreio import db

config = configparser.ConfigParser()
config.read('bot.conf')

TOKEN = config['RASTREIOBOT']['TOKEN']
int_del = int(config['RASTREIOBOT']['int_del'])
LOG_DEL_FILE = config['RASTREIOBOT']['delete_log']

logger = logging.getLogger('InfoLogger')
logger.setLevel(logging.DEBUG)
handler = logging.handlers.TimedRotatingFileHandler(
    LOG_DEL_FILE, when='midnight', interval=1, backupCount=5, encoding='utf-8'
)
logger.addHandler(handler)


def run(dry_run):
    packages = db.all_packages()
    logger.info('--- DELETE running! ---')

    total_deleted = 0
    final_status = [
        'Entrega Efetuada',
        'Objeto entregue ao destinatário',
        'Objeto apreendido por órgão de fiscalização',
        'Objetvo devolvido',
        'Objetvo roubado',
        'Aguardando recebimento pelo ECT.',
        'Objeto não localizado no fluxo postal.',
        'Delivered',
    ]

    for elem in track(list(packages), description="Processing..."):
        code = elem['code']
        time_diff = int(time() - float(elem['time']))
        latest_status = elem['stat'][-1]

        if (
            any(status in latest_status for status in final_status)
            and time_diff > int_del
            or time_diff > 4 * int_del
        ):
            if not dry_run:
                db.delete_package(elem['code'])

            logger.info("%s\t%s\t%r", datetime.now(), elem['code'], latest_status)
            total_deleted += 1

    logger.info("Total of packages deleted: %s", total_deleted)
