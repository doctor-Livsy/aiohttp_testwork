import json
import logging
import os

import jwt
import io

from typing import Tuple, cast
from aiohttp import web
from datetime import datetime, timedelta
from database import Database
from PIL import Image

from utils import image_to_bytes, resize_image, get_file_handler, CustomAccessLogger, route


class AsyncServer:

    __JWT_SECRET = 'super_secured_secret'
    __JWT_ALGORITHM = 'HS256'
    __JWT_EXP_DELTA_SECONDS = 30

    def __init__(self, config: dict, app: web.Application, logger: logging.Logger) -> None:
        self._server_config: dict = config['server_config']
        self._app: web.Application = app
        self._database: Database = Database(config=config['database_config'])
        self._logger: logging.Logger = logger

    def _get_payload(self, data: dict) -> dict:
        payload = {
            'user_id': data['id'],
            'expiration': (datetime.utcnow() + timedelta(seconds=self.__JWT_EXP_DELTA_SECONDS)).timestamp()
        }
        return payload

    def _validate_token(self, token: str) -> Tuple[bool, str]:
        self._logger.info('Checking access token...', extra=route())

        payload = jwt.decode(token, self.__JWT_SECRET, self.__JWT_ALGORITHM)
        current_timestamp = datetime.utcnow().timestamp()
        if payload['expiration'] < current_timestamp:
            self._logger.info('Authorization failed. Token expired', extra=route())
            return False, 'Token expired'

        check_token = jwt.encode(payload, self.__JWT_SECRET, self.__JWT_ALGORITHM)
        if token == check_token:
            self._logger.info('Authorization passed', extra=route())
            return True, 'Authorization passed'
        else:
            self._logger.info('Authorization failed. Invalid token', extra=route())
            return False, 'Invalid token'

    def _create_access_token(self, payload: dict) -> str:
        jwt_token = jwt.encode(payload, self.__JWT_SECRET, self.__JWT_ALGORITHM)
        self._logger.info('Access token has been successful created', extra=route())
        return jwt_token

    async def _handle_and_store_image(
            self, image: Image, image_id: str, quality=None, height=None, width=None, **kwargs
    ) -> Tuple[bool, str]:

        image = cast(Image, image)
        resize_image(image, width, height)

        if image.format != 'JPEG':
            converted_binary_image = image_to_bytes(image, 'JPEG', quality)
        else:
            converted_binary_image = image_to_bytes(image, quality)

        result, message = await self._database.save_binary_image(image_id=image_id, binary_image=converted_binary_image)
        return result, message

    async def _register_user(self, request: web.Request) -> web.Response:
        self._logger.info('Registration request has been received', extra=route(request.path))
        data: dict = await request.json()
        user = data['user_name']

        add_user_result = await self._database.add_user(**data)

        if add_user_result:
            text = f'User "{user}" has been successfully registered'
            self._logger.info(text, extra=route(request.path))
            return web.json_response(text=text)
        else:
            text = f'User "{user}" already exist'
            self._logger.info(text, extra=route(request.path))
            return web.json_response(text=text)

    async def _authenticate(self, request: web.Request) -> web.Response:
        self._logger.info('Authentication request has been received', extra=route(request.path))
        data: dict = await request.json()
        user = data['user_name']
        password = data['password']

        result_db = await self._database.get_user(user)
        if result_db and result_db['user_name'] == user and result_db['password'] == password:
            self._logger.info(f'User "{user} has been successful authenticated', extra=route(request.path))
            response = {
                'status': 'Authenticated',
                'access_token': self._create_access_token(self._get_payload(result_db)),
            }
            return web.json_response(text=json.dumps(response), status=200)
        else:
            self._logger.info(f'User "{user}" has been failed authentication', extra=route(request.path))
            return web.json_response(text=f'Unauthorized', status=401)

    async def _upload_image(self, request: web.Request) -> web.Response:
        self._logger.info('Upload image request has been received', extra=route(request.path))

        token_pass, message = self._validate_token(request.headers['access_token'])
        if not token_pass:
            return web.json_response(text=message, status=403)

        data = await request.read()
        compression_parameters = json.loads(request.headers['CompressionParameters'])
        image_id = request.headers['ImageID']
        image = Image.open(io.BytesIO(data))
        self._logger.info('Image has been received', extra=route(request.path))

        result, message = await self._handle_and_store_image(image, image_id, **compression_parameters)

        if result:
            text = 'Successfully uploaded image to database'
            self._logger.info(text, extra=route(request.path))
            return web.json_response(text=text, status=200)
        else:
            self._logger.info(message, extra=route(request.path))
            return web.json_response(text=message, status=200)

    async def _get_image(self, request: web.Request) -> web.Response:
        self._logger.info('Upload image request has been received', extra=route(request.path))
        token_pass, message = self._validate_token(request.headers['access_token'])
        if not token_pass:
            return web.json_response(text=message, status=403)
        image_id = request.headers['ImageID']

        binary_image = await self._database.get_binary_image(image_id)

        if binary_image:
            self._logger.info(f'Image "{image_id}" has been found and got from database', extra=route(request.path))
            return web.Response(body=binary_image.get('image'), status=200, content_type='application/octet-stream')
        else:
            self._logger.info(f'Image "{image_id}" not found', extra=route(request.path))
            return web.json_response(text=f'Image "{image_id}" not found', status=404)

    async def _get_logs(self, request: web.Request) -> web.Response:
        self._logger.info('Request for logs received', extra=route(request.path))
        token_pass, message = self._validate_token(request.headers['access_token'])
        if not token_pass:
            return web.json_response(text=message, status=403)

        logs = open('logs.log')
        return web.json_response(text=logs.read(), status=200)

    async def _on_startup(self, app: web.Application) -> None:
        # asyncpg create pool
        await self._database.run_database()
        self._logger.info('Database has been successfully initialized', extra=route())
        self._logger.info('Server has been started', extra=route())

    async def _on_shutdown(self, app: web.Application) -> None:
        # Close connections pool
        await self._database.connection_pool.close()
        self._logger.info('Connection pool has been closed', extra=route())

    def _init_handlers(self) -> None:
        self._app.router.add_post('/auth', self._authenticate)
        self._app.router.add_post('/register_user', self._register_user)
        self._app.router.add_post('/api/upload_image', self._upload_image)
        self._app.router.add_get('/api/get_image', self._get_image)
        self._app.router.add_get('/api/get_logs', self._get_logs)
        self._logger.info('Handlers has been initialized', extra=route())

    def _run(self) -> None:
        web.run_app(
            app=self._app,
            host=self._server_config['host'],
            port=self._server_config['port'],
            access_log_class=CustomAccessLogger
        )

    def run(self) -> None:
        # setup routes
        self._init_handlers()

        # init callbacks
        self._app.on_startup.append(self._on_startup)
        self._app.on_shutdown.append(self._on_shutdown)

        self._run()
