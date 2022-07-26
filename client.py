import io
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

image_id = 'test-image-name'

compression_parameters = {
    'quality': 85,
    'height': 400,
    'width': 450
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


async def upload_image(session, access_token):
    headers = {
        'access_token': access_token,
        'Content-Type': 'application/octet-stream',
        'ImageID': image_id,
        'CompressionParameters': json.dumps(compression_parameters)
    }

    image = cast(Image, Image.open('image.png'))
    b_image = image_to_bytes(image)

    response = await session.post('/api/upload_image', data=b_image, headers=headers)
    print(response.status, await response.text())


async def get_image(session, access_token):
    headers = {
        'access_token': access_token,
        'ImageID': image_id,
    }
    response = await session.get('/api/get_image', headers=headers)

    if response.status == 403:
        print('re-Authorization...')
        access_token = await auth(session)
        headers = {
            'access_token': access_token,
            'ImageID': image_id,
        }
        response = await session.get('/api/get_image', headers=headers)

    data = await response.read()

    print('Image has been successful received')
    return Image.open(io.BytesIO(data))


async def get_logs(session, access_token):
    headers = {'access_token': access_token}
    response = await session.get('/api/get_logs', headers=headers)

    if response.status == 403:
        print('re-Authorization...')
        access_token = await auth(session)
        headers = {'access_token': access_token}
        response = await session.get('/api/get_logs', headers=headers)

    return await response.text()


async def main():
    async with aiohttp.ClientSession('http://localhost:8080') as session:
        print('Registration...')
        await registration(session)

        print('Authorization...')
        access_token = await auth(session)

        print('Trying to upload image...')
        await upload_image(session, access_token)

        print('Trying to get image...')
        image = await get_image(session, access_token)

        print('Trying to get logs...')
        logs = await get_logs(session, access_token)
        print(logs)

        image.show()


asyncio.run(main())
