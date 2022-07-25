from aiohttp import web
import yaml

from server import AsyncServer


def load_config(filename: str) -> dict:
    with open(filename) as f:
        config_data = yaml.safe_load(f)
    return config_data


def run() -> None:
    dict_config: dict = load_config('config.yml')
    server = AsyncServer(
        config=dict_config,
        app=web.Application()
    )

    try:
        server.run()
    except Exception as e:
        raise e


if __name__ == "__main__":
    run()
