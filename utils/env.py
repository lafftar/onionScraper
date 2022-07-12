import asyncio
import functools
import sys
from os import listdir
from random import choice

import aiohttp
from aiohttp import ClientTimeout
from colorama import init

from utils import terminal
from utils.base_exceptions import CouldNotGetWorkingProxy
from utils.custom_logger import Log
from utils.data_structs import Proxy
from utils.req_senders import send_req
from utils.root import get_project_root
from utils.terminal import update_title

init()
log = Log(f'[ENV]', do_update_title=False)
terminal.clear()


def line_not_empty(each): return len(each.strip()) > 0
def split_by_comma(each): return [line.strip() for line in each.strip().split(',')]
def strip_each(line): return [item.strip() for item in line.strip().split(',')][:2]


class Env:
    client: aiohttp.ClientSession = None
    log: Log = Log('[ENV]', do_update_title=False)
    update_title('Setting Up Env')

    def __init__(self):
        self.is_running_on_server = True
        # check if in dev, by existence of `.dev` in `~/shapeGen/user_data/`
        if '.dev' in listdir(f'{get_project_root()}/user_data'):
            self.is_running_on_server = False

        self.log.debug(f'Is Running On Server - {self.is_running_on_server}')

        # grab config
        with open(f'{get_project_root()}/user_data/config.csv') as file:
            settings = {
                split_by_comma(line)[0].strip(): split_by_comma(line)[1].strip()
                for line in file.readlines()
                if line_not_empty(line)
            }

        self.refresh_rate = int(settings['REFRESH_RATE'])
        self.log.debug(f'Refresh Rate -> {self.refresh_rate} minutes.')

    @staticmethod
    def increase_limits():
        if sys.platform == 'win32':
            import win32file

            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            win32file._setmaxstdio(8192)

        if sys.platform == 'linux':
            import resource

            before, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            try:
                resource.setrlimit(resource.RLIMIT_NOFILE, (1048576, hard))
            except ValueError:
                log.warn(f'Already at max limit - {before}')

    @staticmethod
    async def check_proxy(proxy: Proxy) -> str | None:
        await Env.create_http_client()
        resp: aiohttp.ClientResponse = await send_req(functools.partial(Env.client.get,
                                                                        url='https://api.ipify.org',
                                                                        proxy=str(proxy),
                                                                        headers={}),
                                                      num_tries=2)
        if not resp:
            return

        ip = await resp.text()
        return ip

    @staticmethod
    async def return_proxy() -> Proxy:
        """
        Pick a proxy randomly, test it and return it.
        :return:
        """
        proxy, ip = None, ''
        await Env.create_http_client()
        for _ in range(10):
            proxy = choice(Env.proxies)
            # proxy = Proxy(host='192.168.0.28', port='4000')
            Env.log.debug(f'Testing - {proxy}.')
            ip: str = await Env.check_proxy(proxy)
            if not ip:
                Env.log.error(f'Test Failed - {proxy}.')
                proxy = None
                continue
            break

        if not ip:
            raise CouldNotGetWorkingProxy
        Env.log.info(f'Test Good - {proxy} - {ip}.')
        return proxy

    @staticmethod
    async def create_http_client():
        if not Env.client:
            ClientTimeout.total = 5.0
            Env.client = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))

    @staticmethod
    async def close_http_client():
        if Env.client:
            await Env.client.close()


ENV = Env()


if __name__ == "__main__":
    asyncio.run(Env.return_proxy())