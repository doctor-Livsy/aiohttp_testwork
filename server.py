import json
import logging
import jwt
import io

from typing import Tuple, cast
from aiohttp import web
from datetime import datetime, timedelta
from database import Database
from PIL import Image

from utils import image_to_bytes, resize_image


class AsyncServer:

    __JWT_SECRET = 'super_secured_secret'
    __JWT_ALGORITHM = 'HS256'
    __JWT_EXP_DELTA_SECONDS = 30

    def __init__(self, config: dict, app: web.Application) -> None:
        self._server_config: dict = config['server_config']
        self._app: web.Application = app
        self._database: Database = Database(config=config['database_config'])
        self._logger: logging.Logger = logging.getLogger(__name__)

    def _get_payload(self, data: dict) -> dict:
        payload = {
            'user_id': data['id'],
            'expiration': (datetime.utcnow() + timedelta(seconds=self.__JWT_EXP_DELTA_SECONDS)).timestamp()
        }
        return payload

    def _validate_token(self, token: str) -> Tuple[bool, str]:
        payload = jwt.decode(token, self.__JWT_SECRET, self.__JWT_ALGORITHM)
        current_timestamp = datetime.utcnow().timestamp()
        if payload['expiration'] < current_timestamp:
            return False, 'Token expired'

        check_token = jwt.encode(payload, self.__JWT_SECRET, self.__JWT_ALGORITHM)
        if token == check_token:
            return True, 'Ok'
        else:
            return False, 'Invalid token'

    def _create_access_token(self, payload: dict) -> str:
        jwt_token = jwt.encode(payload, self.__JWT_SECRET, self.__JWT_ALGORITHM)
        return jwt_token

    async def _handle_and_store_image(
            self, image: Image, quality=None, height=None, width=None, **kwargs
    ) -> Tuple[bool, str]:

        image = cast(Image, image)
        resize_image(image, width, height)

        if image.format != 'jpeg':
            converted_bytes_image = image_to_bytes(image, 'jpeg', quality)
        else:
            converted_bytes_image = image_to_bytes(image, quality)

        result, message = await self._database.save_bytes_image(image_id='2221sdf', bytes_image=converted_bytes_image)
        return result, message

    async def _register_user(self, request: web.Request) -> web.Response:
        data: dict = await request.json()
        user = data['user_name']

        add_user_result = await self._database.add_user(**data)
        if add_user_result:
            return web.json_response(text=f'User "{user}" has been successfully registered')
        else:
            return web.json_response(text=f'User "{user}" already exist')

    async def _authenticate(self, request: web.Request) -> web.Response:
        data: dict = await request.json()
        user = data['user_name']
        password = data['password']

        result_db = await self._database.get_user(user)
        if result_db and result_db['user_name'] == user and result_db['password'] == password:
            response = {
                'status': 'Authorized',
                'access_token': self._create_access_token(self._get_payload(result_db)),
            }
            return web.json_response(text=json.dumps(response), status=200)
        else:
            return web.json_response(text=f'Unauthorized', status=401)

    async def _upload_image(self, request: web.Request) -> web.Response:
        token_pass, message = self._validate_token(request.headers['access_token'])
        if not token_pass:
            return web.json_response(text=message, status=401)

        data = await request.read()
        compression_parameters = json.loads(request.headers['CompressionParameters'])
        image = Image.open(io.BytesIO(data))

        result, message = await self._handle_and_store_image(image, **compression_parameters)
        if result:
            return web.json_response(text='Successfully upload image', status=200)
        else:
            return web.json_response(text=message, status=200)

    async def _get_image(self, request: web.Request) -> web.Response:
        token_pass, message = self._validate_token(request.headers['access_token'])
        if not token_pass:
            return web.json_response(text=message, status=401)

        data: dict = await request.json()
        return web.json_response(data={'ok': 200})

    async def _on_startup(self, app: web.Application) -> None:
        # asyncpg create pool
        await self._database.run_database()

    async def _on_shutdown(self, app: web.Application) -> None:
        # Close connections pool
        await self._database.connection_pool.close()

    def _init_handlers(self) -> None:
        self._app.router.add_post('/auth', self._authenticate)
        self._app.router.add_post('/register_user', self._register_user)
        self._app.router.add_post('/api/upload_image', self._upload_image)
        self._app.router.add_get('/api/get_image', self._get_image)

    def _run(self) -> None:
        web.run_app(
            app=self._app,
            host=self._server_config['host'],
            port=self._server_config['port']
        )

    def run(self) -> None:
        # setup routes
        self._init_handlers()

        # init callbacks
        self._app.on_startup.append(self._on_startup)
        self._app.on_shutdown.append(self._on_shutdown)

        self._run()
