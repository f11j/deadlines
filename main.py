#!/usr/bin/env python
import asyncio
import logging
import logging.handlers
import os
import sys
from enum import StrEnum
from typing import Any
from typing import Optional

from pyrogram.client import Client
from pyrogram.enums import ParseMode
from pyrogram.sync import idle


# region environment-variables
class RequiredEnviron(StrEnum):
    TGCLIENT_ENABLE = "DEADLINES_TGCLIENT_ENABLE"
    APP_NAME = "DEADLINES_API_APP_TITLE"
    API_ID = "DEADLINES_API_ID"
    API_HASH = "DEADLINES_API_HASH"


class OptionalEnviron(StrEnum):
    ASYNCIO_DEBUG = "DEADLINES_ASYNCIO_DEBUG"
    LOG_ENABLE = "DEADLINES_LOG_ENABLE"
    LOG_FILE = "DEADLINES_LOG_FILE"
    LOG_FILEMODE = "DEADLINES_LOG_FILEMOD"
    LOG_LEVEL = "DEADLINES_LOG_LEVEL"


def get_environ_if(condition: bool, varname: str) -> Optional[str]:
    logging.debug(f"{condition=}, {varname=}")
    if condition:
        return os.getenv(varname)
    return None

# endregion environment-variables


# region settings
class LogConfig:
    """Logging configuraion settings"""

    # Load environment variables
    ENABLE = bool(os.getenv(OptionalEnviron.LOG_ENABLE))
    FILE = get_environ_if(ENABLE, OptionalEnviron.LOG_FILE)
    FILEMODE = get_environ_if(ENABLE, OptionalEnviron.LOG_FILEMODE) or "a+"
    LEVEL = get_environ_if(ENABLE, OptionalEnviron.LOG_LEVEL) or logging.CRITICAL

    # LEVEL: Validate textual or numeric representation of logging level
    if isinstance(LEVEL, int) and LEVEL in logging._levelToName:
        LEVEL = logging._levelToName[LEVEL]
    elif isinstance(LEVEL, str):
        if (lvl := LEVEL.upper()) in logging._nameToLevel:
            LEVEL = lvl
        elif LEVEL.isdigit() and (lvl := int(LEVEL)) in logging._levelToName:  # type: ignore
            LEVEL = logging._levelToName[lvl]  # type: ignore
        else:
            assert False, (OptionalEnviron.LOG_LEVEL, LEVEL)
    else:
        assert False, (OptionalEnviron.LOG_LEVEL, LEVEL)

    # TODO: validate others


class TGConfig:
    """Telegram configuration settings"""

    # Load environment variables
    ENABLE = bool(os.getenv(RequiredEnviron.TGCLIENT_ENABLE))
    APP_NAME = get_environ_if(ENABLE, RequiredEnviron.APP_NAME)
    API_ID = get_environ_if(ENABLE, RequiredEnviron.API_ID)
    API_HASH = get_environ_if(ENABLE, RequiredEnviron.API_HASH)
    ASYNCIO_DEBUG = bool(os.getenv(OptionalEnviron.ASYNCIO_DEBUG))

    if isinstance(API_ID, str) and API_ID.isdigit():
        API_ID = int(API_ID)  # type: ignore
    else:
        assert False, (RequiredEnviron.API_ID, API_ID)
    assert APP_NAME, (RequiredEnviron.APP_NAME, APP_NAME)
    assert API_HASH, (RequiredEnviron.API_HASH, API_HASH)

    # TODO: validate variables

    @staticmethod
    def client_kwargs() -> dict:
        """`pyrogram.Client(**TGConfig().client_kwargs())`"""
        return {
            "name": TGConfig.APP_NAME,
            "api_id": TGConfig.API_ID,
            "api_hash": TGConfig.API_HASH,
        }

    @staticmethod
    def main_args() -> dict:
        """`main(**TGConfig.main_args())`"""
        return {
            "enable_tgclient": TGConfig.ENABLE,
        }

    @staticmethod
    def finish() -> dict:
        """`finish(**TGConfig.finish())`"""
        return {}

# endregion settings


class Cache:
    class Keys(StrEnum):
        TGCLIENT = "tgclient"

    __cache = {
        Keys.TGCLIENT.value: None
    }

    @staticmethod
    async def get(key: str) -> Any:
        return Cache.__cache[key]

    @staticmethod
    async def add(key: str, value: Any) -> None:
        Cache.__cache[key] = value


# region logging
async def initialize_logger(logfile=LogConfig.FILE, mode=LogConfig.FILEMODE) -> logging.Logger:
    """Create `logfile` if not exists and create logger (`RotatingFileHandler`,`StreamHandler`)"""

    # TODO: Create DEADLINES_LOG_THIRD_PARTY_LEVEL ?
    for _ in logging.root.manager.loggerDict:
        logging.getLogger(_).setLevel(logging.INFO)

    os.makedirs(os.path.dirname(logfile), exist_ok=True)

    console_format_str = "[%(levelname)s] - %(name)s - (%(filename)s::%(funcName)s:%(lineno)d) - %(message)s"
    file_format_str = "%(asctime)s - [%(levelname)s] - %(name)s - %(filename)s:%(lineno)d::%(funcName)s - %(message)s"

    rotating_file_handler = logging.handlers.RotatingFileHandler(
        logfile,
        mode=mode,
        maxBytes=1024 * 1024,
        backupCount=5,
    )

    class ConditionalFormatter(logging.Formatter):
        def format(self, record) -> str:
            """Disable Format for smth messages"""
            if hasattr(record, "simple") and getattr(record, "simple", False):
                result = record.getMessage()
            else:
                result = logging.Formatter.format(self, record)
            return result

    rotating_file_handler_formatter = ConditionalFormatter(file_format_str)
    rotating_file_handler.setFormatter(rotating_file_handler_formatter)
    rotating_file_handler.setLevel(LogConfig.LEVEL)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler_formatter = logging.Formatter(console_format_str)
    console_handler.setFormatter(console_handler_formatter)
    console_handler.setLevel(logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(LogConfig.LEVEL)
    root_logger.addHandler(rotating_file_handler)
    root_logger.addHandler(console_handler)

    return root_logger

# endregion logging


# region tgclient
async def initialize_tgclient(name: str, *, api_id: int, api_hash: str, parse_mode=ParseMode.HTML) -> Client:
    """Initialize pyrogram.Client and store the object in the cache"""
    logging.debug(f"{locals()}")
    tg_client = Client(name=name, api_id=api_id, api_hash=api_hash, parse_mode=parse_mode)
    await Cache.add(Cache.Keys.TGCLIENT, tg_client)
    logging.debug("Pyrogram client '%s' initialized and cached", name)
    return tg_client


async def prepare_tgclient(**init_kw: dict) -> Client:
    """Create pyrogram.Client and [...]"""
    logging.debug(f"{init_kw=}")
    tg_client = await initialize_tgclient(**(init_kw or TGConfig.client_kwargs()))
    return tg_client


async def prepare_tgclient_if(condition: bool, **init_kw: dict) -> Optional[Client]:
    logging.debug(f"{condition=}, {init_kw=}")
    if condition:
        tg_client = await prepare_tgclient(**init_kw)
        return tg_client
    return None

# endregion tgclient


async def start_manager(enable_tgclient: bool = False) -> None:
    """Start manager with enabled components"""
    tg_client = await prepare_tgclient_if(enable_tgclient)
    if tg_client is not None and not tg_client.is_connected:
        await tg_client.start()  # and wait updates...
    await idle()


def finish(**kw):
    """Implement me"""
    logging.info(f"{kw=}")


async def main(**kwargs: dict) -> None:
    """Entry point. Start manager with args,kwargs"""
    if LogConfig.ENABLE:
        await initialize_logger()
    logging.info(f"{kwargs=}")
    await start_manager(**kwargs)  # type: ignore


try:
    asyncio.run(main=main(**TGConfig.main_args()), debug=TGConfig.ASYNCIO_DEBUG)
finally:
    finish(**TGConfig.finish())
