from dataclasses import dataclass


@dataclass
class ServerConfig:
    host: str = '0.0.0.0'
    port: int = 8080


@dataclass
class CommonConfig:
    server_config: ServerConfig = ServerConfig
