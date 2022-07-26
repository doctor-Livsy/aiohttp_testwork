from typing import Optional, Tuple

import asyncio
import asyncpg
from asyncpg.exceptions import UniqueViolationError


class Database:

    def __init__(self, config: dict) -> None:
        self.config: dict = config
        self.connection_pool: Optional[asyncpg.Pool] = None

    @staticmethod
    def format_args(sql, parameters: dict) -> tuple:
        sql += " AND ".join([f"{item} = ${num}" for num, item in enumerate(parameters, start=1)])
        return sql, tuple(parameters.values())

    @staticmethod
    def args_to_string(*args) -> str:
        string = ''
        for arg in args:
            string += arg + ', '
        return string[:-2]

    @staticmethod
    def parameters_to_string(dictionary: dict) -> str:
        string = ''
        for key, value in zip(dictionary.keys(), dictionary.values()):
            string += f'{key} = {value}, '

        return string[:-2]

    async def create_users_table(self) -> None:
        request = """
                CREATE TABLE IF NOT EXISTS users(
                ID  SERIAL PRIMARY KEY,
                user_name VARCHAR(255),
                password VARCHAR(255),
                UNIQUE(user_name))
                """

        async with self.connection_pool.acquire() as connection:
            await connection.execute(request)

    async def create_images_table(self) -> None:
        request = """
                CREATE TABLE IF NOT EXISTS images(
                ID  SERIAL PRIMARY KEY,
                image_id VARCHAR(255),
                image BYTEA,
                UNIQUE(image_id))
                """

        async with self.connection_pool.acquire() as connection:
            await connection.execute(request)

    async def get_user(self, user_name: str):
        request = f"SELECT * FROM users WHERE user_name=$1"
        return await self.connection_pool.fetchrow(request, user_name)

    async def add_user(self, user_name: str, password: str) -> bool:
        request = "INSERT INTO users(user_name, password) VALUES ($1, $2)"
        async with self.connection_pool.acquire() as connection:
            user = await self.get_user(user_name=user_name)
            if user is None:
                await connection.execute(request, user_name, password)
                return True
        return False

    async def save_binary_image(self, image_id: str, binary_image: bytes) -> Tuple[bool, str]:
        request = 'INSERT INTO images(image_id, image) VALUES ($1, $2)'
        try:
            await self.connection_pool.execute(request, image_id, binary_image)
            return True, ''
        except UniqueViolationError:
            return False, f'image_id: {image_id} already exist'
        except Exception as e:
            raise e

    async def get_binary_image(self, image_id: str):
        request = f"SELECT * FROM images WHERE image_id=$1"
        return await self.connection_pool.fetchrow(request, image_id)

    async def run_database(self) -> None:
        self.connection_pool = await asyncpg.create_pool(
            database=self.config['POSTGRES_DB'],
            user=self.config['POSTGRES_USER'],
            password=self.config['POSTGRES_PASSWORD'],
            host=self.config['POSTGRES_HOST']
        )

        await self.create_users_table()
        await self.create_images_table()

