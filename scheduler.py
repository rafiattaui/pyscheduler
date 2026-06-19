from abc import ABC, abstractmethod
from process import Process

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

class FCFS(BaseScheduler):
    # first come first serve
    # new processes are added to the end,
    # the process at the front of the queue is selected for execution

    def __init__(self):
        self.readyqueue = []
    
    def select_next(self) -> Process:
        return self.readyqueue.pop()

    def add_process(self, process: Process):
        self.readyqueue.append(process)

    def is_empty(self) -> bool:
        return bool(self.readyqueue)
    
    def __repr__(self):
        return f"FCFS Scheduler, Ready Queue: {self.readyqueue}"

