from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')

class IService(ABC):
    @abstractmethod
    def execute(self, action: str, data: dict):
        pass