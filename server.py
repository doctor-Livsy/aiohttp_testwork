from aiohttp import web


class AsyncServer:

    def __init__(self, config: dict, app: web.Application) -> None:
        self.server_config: dict = config['server_config']
        self.app: web.Application = app

    async def _on_startup(self) -> None:
        # asyncpg create pool
        pass

    async def _on_shutdown(self) -> None:
        # Close connections pool
        pass

    def _run(self) -> None:
        web.run_app(
            app=self.app,
            host=self.server_config['host'],
            port=self.server_config['port']
        )

    def run(self) -> None:
        # setup routes
        print('')

        # init callbacks
        self.app.on_startup.append(self._on_startup)
        self.app.on_shutdown.append(self._on_shutdown)

        self._run()
