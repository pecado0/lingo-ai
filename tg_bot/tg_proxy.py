import asyncio
import sys
import aiohttp
import warnings      
import logging  
from aiogram.client.session.aiohttp import AiohttpSession

warnings.simplefilter('ignore', ResourceWarning)
logging.getLogger('asyncio').setLevel(logging.CRITICAL)

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class SystemProxySession(AiohttpSession):
    async def create_session(self) -> aiohttp.ClientSession:
        connector = aiohttp.TCPConnector(ssl=False) 
        return aiohttp.ClientSession(
            connector=connector,
            trust_env=True,
            json_serialize=self.json_dumps
        )