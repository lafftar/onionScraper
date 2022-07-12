import asyncio

import httpx
from httpx_socks import AsyncProxyTransport

from utils.custom_logger import Log
from utils.tools import print_req_info


log: Log = Log('[OS]')


async def test_tor():
    transport = AsyncProxyTransport.from_url('socks5://localhost:9051')

    req: httpx.Request = httpx.Request(
        method='GET',
        url='https://check.torproject.org/'
    )

    async with httpx.AsyncClient(transport=transport) as c:
        c: httpx.AsyncClient
        resp: httpx.Response = await c.send(req)

    if 'Congratulations. This browser is configured to use Tor.' not in resp.text:
        print_req_info(resp, True, True)
        raise Exception("Tor Test Failed.")

    log.info('Tor Test Good.')


if __name__ == "__main__":
    asyncio.run(test_tor())
