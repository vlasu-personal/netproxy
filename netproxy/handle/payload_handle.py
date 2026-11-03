import abc


class PayloadHandle(abc.ABC):
    @abc.abstractmethod
    def execute(self, payload: bytes) -> bytes:
        pass
