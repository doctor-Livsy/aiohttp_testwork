from typing import cast

import asyncio
import aiohttp
import json
from PIL import Image

from utils import image_to_bytes

creds = {
    'user_name': 'test_user',
    'password': 'test_password'
}


async def registration(session):
    headers = {'Content-Type': 'application/json'}
    response = await session.post('/register_user', json=creds, headers=headers)
    message = await response.text()
    print(f'Code: {response.status}. Message: {message}')


async def auth(session):
    headers = {'Content-Type': 'application/json'}
    response = await session.post('/auth', json=creds, headers=headers)
    message = json.loads(await response.text())

    print(f'Code: {response.status}. Message: {message}')

    return message['access_token']


async def main():
    async with aiohttp.ClientSession('http://localhost:8080') as session:
        print('Registration...')
        await registration(session)

        print('Authorization...')
        access_token = await auth(session)

        ###### UPLOAD IMAGE ######

        parameters = {
            'quality': 95,
            'height': 200,
            'width': 500
        }

        headers = {
            'access_token': access_token,
            'Content-Type': 'application/octet-stream',
            'CompressionParameters': json.dumps(parameters)
        }

        image = cast(Image, Image.open('image.png'))
        b_image = image_to_bytes(image)

        response = await session.post('/api/upload_image', data=b_image, headers=headers)
        print(response.status, await response.text())

        ######## GET IMAGE ########


asyncio.run(main())
