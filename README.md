# Aiohttp testwork


Тестовый шаблон для тестирования api на базе aiohttp и postgresql. Окружение можно установить с помощью poetry 
(командой _poetry install_). База данных поднимается в докере:

_docker run -p 5432:5432 -e POSTGRES_PASSWORD=password -e POSTGRES_USER=root -e POSTGRES_DB=database -d postgres:14.4_

Сервер запускается через _run.py_. При инициализации базы данных все схемы создаются автоматически (если база пустая). 


### Маршруты

- `/register_user` - (POST) Запись юзера в БД. Параметры:
  * Логин (header - _user_name_)
  * Пароль (header - _password_)

- `/auth` - (POST) Аутентификация и получение access token. Параметры:
  * Логин (header - _user_name_)
  * Пароль (header - _password_)

Для представленных ниже маршрутов требуется заголовок с access token (header - _access_token_).

- `/api/upload_image` - (POST) Загрузка изображения на сервер. Параметры:
  * Идентификатор изображения (header - _ImageID_)
  * Параметры сжатия (header - _CompressionParameters_). Словарь с ключами:
    * _quality_: int в %
    * _height_: int
    * _width_: int

- `/api/get_image` - (GET) Загрузка изображения с сервера. Параметры:
  * Идентификатор изображения (header - _ImageID_)

- `/api/get_logs'` - (GET) Получение логов


### Конфигурация

YAML файл с конфигурацией - _config.yml_
 - `server_config` - Хост и порт для сервера
 - `database_config` - Учетные данные для подключения к БД


### Клиент

Файл с тестовым клиентом - _client.py_. Клиент проходится по всем маршрутам: выполняет регистрацию пользователя,
аутентификацию и получение access token, загрузку изображения на сервер, выгрузку изображения с сервера и получение логов.
