import asyncio
import functools
from asyncio import sleep
import aiohttp
import anyio
import httpx
from aiohttp import client_exceptions


async def send_req(req_obj: functools.partial, num_tries: int = 5) -> \
        httpx.Response | aiohttp.ClientResponse | None:
    """
    Central Request Handler. All requests should go through this.
    :param num_tries:
    :param req_obj:
    :return:
    """
    for _ in range(num_tries):
        try:
            item = await req_obj()
            return item
        except (
                # httpx errors
                httpx.ConnectTimeout, httpx.ProxyError, httpx.ConnectError,
                httpx.ReadError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.RemoteProtocolError,

                # aiohttp errors
                asyncio.exceptions.TimeoutError, client_exceptions.ClientHttpProxyError,
                client_exceptions.ClientProxyConnectionError,
                client_exceptions.ClientOSError,
                client_exceptions.ServerDisconnectedError,

                # any io errors
                anyio.ClosedResourceError
                ):
            await sleep(2)
    return


async def tls_send(req: httpx.Request, client: httpx.AsyncClient, proxies: str = '') -> httpx.Response | None:
    """
    Just for the TLS.
    :param proxies:
    :param client:
    :param req:
    :return:
    """
    old_url = str(req.url)
    req.headers['poptls-url'] = old_url
    # {choice(TLS_PORTS)}
    req.url = httpx.URL(f'http://localhost:6000')
    if proxies:
        req.headers['poptls-proxy'] = proxies
    res: httpx.Response = await send_req(functools.partial(client.send, req), num_tries=5)
    req.headers.pop('poptls-url')
    req.headers.pop('poptls-proxy', None)
    req.url = old_url
    return res
