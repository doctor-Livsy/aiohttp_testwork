import io
import logging

from PIL import Image
from aiohttp.abc import AbstractAccessLogger


def image_to_bytes(image, image_format=None, quality=None) -> bytes:
    image_format = image.format if not image_format else image_format
    b_image = io.BytesIO()
    image.save(b_image, format=image_format, quality=quality)
    return b_image.getvalue()


def resize_image(image, width, height) -> Image:
    width = image.width if not width else width
    height = image.height if not height else height
    image.thumbnail(size=(width, height))


def get_file_handler():
    file_handler = logging.FileHandler("logs.log")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s, %(msecs)d: %(route)s: %(funcName)s: %(levelname)s: %(message)s')
    file_handler.setFormatter(formatter)
    return file_handler


def route(route_path: str = '') -> dict:
    return {'route': route_path}


class CustomAccessLogger(AbstractAccessLogger):
    def log(self, request, response, time):
        self.logger.info(f'{request.method} {request.path} done in {round(time, 4)}s: {response.status}')

