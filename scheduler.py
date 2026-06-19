from abc import ABC, abstractmethod

class BaseScheduler(ABC):

    @abstractmethod
    def select_next(self):
        pass

    @abstractmethod
    def add_process(self):
        pass

    @abstractmethod
    def is_empty(self):
        pass

