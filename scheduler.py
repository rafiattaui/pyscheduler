from abc import ABC, abstractmethod
from process import Process
import logging

logger = logging.getLogger(__name__)

class BaseScheduler(ABC):

    @abstractmethod
    def select_next(self):
        pass

    @abstractmethod
    def add_process(self, process: Process):
        pass

    @abstractmethod
    def is_empty(self):
        pass


class FCFS(BaseScheduler):
    # first come first serve
    # new processes are added to the end,
    # the process at the front of the queue is selected for execution

    def __init__(self):
        self.readyqueue = []

    def select_next(self) -> Process:
        return self.readyqueue.pop(0)

    def add_process(self, process: Process):
        self.readyqueue.append(process)

    def is_empty(self) -> bool:
        return len(self.readyqueue) == 0

    def __repr__(self):
        return f"FCFS Scheduler, Ready Queue: {self.readyqueue}"


if __name__ == "__main__":
    scheduler = FCFS()
