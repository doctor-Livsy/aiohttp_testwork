import logging
import yaml

from aiohttp import web
from server import AsyncServer
from utils import get_file_handler


def load_config(filename: str) -> dict:
    with open(filename) as f:
        config_data = yaml.safe_load(f)
    return config_data


def run() -> None:
    dict_config: dict = load_config('config.yml')

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('ServerLogs')
    logger.addHandler(get_file_handler())

    server = AsyncServer(
        config=dict_config,
        app=web.Application(),
        logger=logger
    )

    try:
        server.run()
    except Exception as e:
        raise e


if __name__ == "__main__":
    run()
