from environs import Env
from dataclasses import dataclass


@dataclass
class Bots:
    bot_token: str


@dataclass
class Host:
    host_value: str


@dataclass
class User:
    user_value: str


@dataclass
class Password:
    pass_value: str


@dataclass
class Database:
    database_value: str


@dataclass
class Chat:
    chat_id: int


@dataclass
class Settings:
    bots: Bots
    host: Host
    user: User
    password: Password
    database: Database
    chat: Chat


def get_settings(path: str):
    env = Env()
    env.read_env(path)
    return Settings(
        bots=Bots(
            bot_token=env.str("TOKEN")
        ),
        host=Host(
            host_value=env.str("HOST")
        ),
        user=User(
            user_value=env.str("USER_BD")
        ),
        password=Password(
            pass_value=env.str("PASSWORD")
        ),
        database=Database(
            database_value=env.str("DATABASE")
        ),
        chat=Chat(
            chat_id=env.str("CHAT_ID")
        )
    )


settings = get_settings("settings")
