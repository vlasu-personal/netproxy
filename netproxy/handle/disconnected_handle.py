import abc


class DisconnectedHandle(abc.ABC):
    @abc.abstractmethod
    def disconnected(self) -> None:
        pass
