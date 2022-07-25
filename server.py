import json
import logging
import jwt

from aiohttp import web
from datetime import datetime, timedelta
from database import Database


JWT_SECRET = 'super_secured_secret'
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = 30

# jwt.decode(encoded_jwt, "secret", algorithms=["HS256"])


def create_access_token(payload: dict) -> dict:
    jwt_token = jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)
    return {'access_token': jwt_token}


class AsyncServer:

    def __init__(self, config: dict, app: web.Application) -> None:
        self._server_config: dict = config['server_config']
        self._app: web.Application = app
        self._database: Database = Database(config=config['database_config'])
        self._logger: logging.Logger = logging.getLogger(__name__)

    @staticmethod
    def _get_payload(data: dict) -> dict:
        payload = {
            'user_id': data['id'],
            'expiration': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
        }
        return payload

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

        result_db = await self._database.check_user_exist(user)
        if result_db and result_db['user_name'] == user and result_db['password'] == password:

            result = {
                'ok': 200,
                'access_token': 'fasrgat43q23424rt34tergferg',
            }
            # TODO: вставить функцию выдачи токена
            return web.json_response(text=json.dumps(result))
        else:
            return web.json_response(text=f'Unknown user "{user}"')

    async def _download_info(self, request) -> web.Response:
        return web.json_response(data={'ok': 200})

    async def _get_info(self, request) -> web.Response:
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
        self._app.router.add_post('/api/download_info', self._download_info)
        self._app.router.add_get('/api/get_info', self._get_info)

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
