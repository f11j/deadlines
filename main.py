#!/usr/bin/env python
import asyncio
import os
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


def get_environ_if(condition: bool, varname: str) -> Optional[str]:
    if condition:
        return os.getenv(varname)
    return None

# endregion environment-variables


# region settings
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


# region tgclient
async def initialize_tgclient(name: str, *, api_id: int, api_hash: str, parse_mode=ParseMode.HTML) -> Client:
    """Initialize pyrogram.Client and store the object in the cache"""
    tg_client = Client(name=name, api_id=api_id, api_hash=api_hash, parse_mode=parse_mode)
    await Cache.add(Cache.Keys.TGCLIENT, tg_client)
    return tg_client


async def prepare_tgclient(**init_kw: dict) -> Client:
    """Create pyrogram.Client and [...]"""
    tg_client = await initialize_tgclient(**(init_kw or TGConfig.client_kwargs()))
    return tg_client


async def prepare_tgclient_if(condition: bool, **init_kw: dict) -> Optional[Client]:
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


async def main(**kwargs: dict) -> None:
    """Entry point. Start manager with args,kwargs"""
    await start_manager(**kwargs)  # type: ignore


try:
    asyncio.run(main=main(**TGConfig.main_args()), debug=TGConfig.ASYNCIO_DEBUG)
finally:
    finish(**TGConfig.finish())
