import io
from PIL import Image


def image_to_bytes(image, image_format=None, quality=None) -> bytes:
    image_format = image.format if not image_format else image_format
    b_image = io.BytesIO()
    image.save(b_image, format=image_format, quality=quality)
    return b_image.getvalue()


def resize_image(image, width, height) -> Image:
    width = image.width if not width else width
    height = image.height if not height else height
    image.thumbnail(size=(width, height))

