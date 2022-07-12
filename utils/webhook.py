import asyncio
from asyncio import sleep
import aiohttp
from discord import Colour, Embed, AsyncWebhookAdapter, Webhook

from utils.custom_logger import logger


async def send_webhook(embed_dict, title: str = '', webhook_url: str = None, color: Colour = None,
                       title_link='https://discord.com'):
    if not color:
        color = Colour.dark_red()
    if not webhook_url:
        webhook_url = 'https://discord.com/api/webhooks/961517487961301022/' \
                      'wkeUwhKNeDXOa9Z73c1fSR2kqPZ62TJV0zWjLmt6EcpG23xUKPZTnm06jonPH6Cb3cJb'

    # create embed
    embed = Embed(title=title, color=color, url=title_link)
    embed.set_footer(text='WINX4 Bots - winwinwinwin#0001',
                     icon_url='https://images6.alphacoders.com/909/thumb-1920-909641.png')
    for key, value in embed_dict.items():
        embed.add_field(name=f'{key}', value=f'{value}', inline=False)

    async with aiohttp.ClientSession() as webhook_client:
        for _ in range(3):
            try:
                webhook = Webhook.from_url(
                    url=webhook_url,
                    adapter=AsyncWebhookAdapter(webhook_client))
                await webhook.send(username='S Gen',
                                   avatar_url=
                                   'https://i.pinimg.com/originals/09/17/04/0917045fcee27f48e768680d1f800577.jpg',
                                   embed=embed,
                                   )
                break
            except Exception:
                logger().exception('Webhook Failed')
                await sleep(2)
