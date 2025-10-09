from abc import ABC, abstractmethod


class BaseTransport(ABC):
    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def send_receive(self, data: bytes, timeout: float):
        pass

    @abstractmethod
    async def send(self, data: bytes):
        pass

    @abstractmethod
    async def receive(self) -> bytes:
        pass

    @abstractmethod
    async def close(self):
        pass
