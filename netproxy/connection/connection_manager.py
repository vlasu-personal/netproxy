import abc
from typing import Optional
from . import connection_driver


class ConnectionManager(abc.ABC):
    @abc.abstractmethod
    def enable_server(self, address: str, port: int) -> None:
        pass

    @abc.abstractmethod
    def disable_server(self) -> None:
        pass

    @abc.abstractmethod
    def listen_for_client(self, timeout_s: int) -> Optional[connection_driver.ConnectionDriver]:
        pass

    @abc.abstractmethod
    def connect_host(self, host: str, port: int, timeout_s: int) -> Optional[connection_driver.ConnectionDriver]:
        pass
