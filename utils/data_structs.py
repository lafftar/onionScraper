from dataclasses import dataclass, astuple
from typing import NamedTuple

from playwright.async_api import ProxySettings


class Proxy:
    def __init__(self, host: str, port: str, username: str = '', password: str = '', protocol: str = 'http'):
        self.host: str = host
        self.port: str = port
        self.username: str = username
        self.password: str = password
        self.protocol: str = protocol

    def __str__(self) -> str:
        if self.password:
            return f'{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}'
        return f'{self.protocol}://{self.host}:{self.port}'

    @staticmethod
    def from_playwright_fmt(proxy: ProxySettings):
        """
        Converts from playwright fmt to this.
        :param proxy:
        :return: this Proxy object
        """
        user = proxy.get('username')
        passwd = proxy.get('password')
        server = proxy.get('server').split('://')
        protocol = server[0]
        server = server[1]
        host, port = server.split(':')
        return Proxy(host=host, port=port, username=user, password=passwd, protocol=protocol)


@dataclass
class Resp:
    body: str | bytes = None
    headers: dict = None
    status: int = 200

    def __iter__(self):
        return iter(astuple(self))

    @property
    def to_pw(self):
        return {'status': self.status, 'headers': self.headers, 'body': self.body}
