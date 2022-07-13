import asyncio
import re
from asyncio import sleep
from json import dumps
from time import perf_counter, time

import httpx
from colorama import Back, Fore
from httpx_socks import AsyncProxyTransport

from utils.custom_logger import Log
from utils.terminal import color_wrap
from utils.tools import print_req_info


log: Log = Log('[OS]')


async def return_client():
    # eventually, let this be a pool. @todo
    transport = AsyncProxyTransport.from_url('socks5://localhost:9051')
    return httpx.AsyncClient(transport=transport, verify=False)


async def test_tor():
    req: httpx.Request = httpx.Request(
        method='GET',
        url='https://check.torproject.org/'
    )

    async with await return_client() as c:
        c: httpx.AsyncClient
        resp: httpx.Response = await c.send(req)

    if 'Congratulations. This browser is configured to use Tor.' not in resp.text:
        print_req_info(resp, True, True)
        raise Exception("Tor Test Failed.")

    log.info('Tor Test Good.')


"""
These functions simply scrape all urls it finds, if the url is .onion url, it tries to go there and do the same thing.
A very basic crawler.
"""

q: asyncio.Queue[tuple[str, int]] = asyncio.Queue()  # url, depth | (http://spfio.onion, 3)
seen_urls: dict = {}
last_request_sent_ts = time()  # this will be reset up until the last request gets sent
file_writer_sem: asyncio.Semaphore = asyncio.Semaphore(1)
req_sem: asyncio.Semaphore = asyncio.Semaphore(100)  # max number of requests at any time.


async def write_to_file():
    def _write_to_file():
        # write seen urls to file
        with open('urls.txt', 'w') as file:
            file.write(dumps(seen_urls, indent=4))

    async with file_writer_sem:
        await asyncio.get_event_loop().run_in_executor(None, _write_to_file)


async def parse_urls(url: str, html: str, level: int = 1):
    """
    Parses urls present in the html and adds it to the global q
    :return:
    """
    urls = list(set(re.findall(r'[\w]{16,56}\.onion', html)))
    if not urls:
        return

    for url in urls:
        if not seen_urls.get(url):
            url = f'http://{url}/'
            q.put_nowait((url, level))
            seen_urls[url] = level

    asyncio.create_task(write_to_file())

    log.debug(color_wrap(f"Added {len(urls)} urls to q at depth level {level}.") + "\n\t"
              + color_wrap(f"[URL: {url}]", back_color=Back.MAGENTA, fore_color=Fore.BLACK))


async def crawl(url: str, level: int):
    t1 = perf_counter()

    req: httpx.Request = httpx.Request(
        method='GET',
        url=url
    )

    async with req_sem:
        async with await return_client() as c:
            global last_request_sent_ts
            last_request_sent_ts = time()

            try:
                resp: httpx.Response = await c.send(req)
            except Exception as e:
                log.error(f'{type(e).__name__} {e.args}')
                return

    await parse_urls(url, resp.text,
                     level + 1  # ensure the level always gets incremented from the last
                     )
    log.info(f'Took {perf_counter() - t1:.2f}s to fetch and parse url at depth level {level}.')


async def run():
    # get the page url
    # use regex to get all the urls at once
    # feed that into a global task q
    home_url = "http://6nhmgdpnyoljh5uzr5kwlatx2u3diou4ldeommfxjz3wkhalzgjqxzqd.onion/"
    seen_urls[home_url] = 0

    await crawl(home_url, 0)

    if not seen_urls:
        raise Exception("No urls grabbed from home url. Crawl cannot continue.")

    # begin crawl process
    while time() - last_request_sent_ts < 60:
        if q.empty():
            await sleep(1)  # wait for requests to return
            continue

        asyncio.create_task(
            crawl(*q.get_nowait())
        )

    # we're done when there is nothing in the q, we've reached max depth and all requests/parsing has finalized.

if __name__ == "__main__":
    asyncio.run(run())
