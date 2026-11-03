import abc
from typing import Callable


class ConnectionDriver(abc.ABC):
    @abc.abstractmethod
    def disconnect(self) -> None:
        pass

    @abc.abstractmethod
    def send(self, payload: bytes) -> None:
        pass

    @abc.abstractmethod
    def on_receive(self, cb: Callable[[bytes], None]) -> None:
        pass

    @abc.abstractmethod
    def on_disconnected(self, cb: Callable[[None], None]) -> None:
        pass
