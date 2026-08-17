import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp_socks import ProxyConnector
from config import settings

dp = Dispatcher()


class Socks5AiohttpSession(AiohttpSession):
    """Кастомная сессия aiogram с поддержкой SOCKS5 прокси через aiohttp-socks."""
    def __init__(self, proxy_url: str, **kwargs):
        super().__init__(**kwargs)
        self.proxy_url = proxy_url

    async def create_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = ProxyConnector.from_url(self.proxy_url)
            self._session = aiohttp.ClientSession(
                connector=connector,
                json_serialize=self.json_dumps,
            )
        return self._session


def init_bot() -> Bot:
    if settings.USE_PROXY and settings.SOCKS5_PROXY:
        session = Socks5AiohttpSession(proxy_url=settings.SOCKS5_PROXY)
        return Bot(token=settings.BOT_TOKEN, session=session)
    return Bot(token=settings.BOT_TOKEN)