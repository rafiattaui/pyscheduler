from abc import ABC, abstractmethod
from process import Process
import logging
import heapq

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

    @abstractmethod
    def should_preempt(self, current_process: Process, new_process: Process):
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
    
    def should_preempt(self, current_process, new_process):
        return False # FCFS never preempts

    def __repr__(self):
        return f"FCFS Scheduler, Ready Queue: {self.readyqueue}"
    
class SJF(BaseScheduler):
    # shortest job first
    # use a min-heap that maintains 
    def __init__(self, preemptive: bool = False):
        self.readyqueue = []
        self.preemptive = preemptive

    def select_next(self):
        return heapq.heappop(self.readyqueue)

    def add_process(self, process: Process):
        # heap uses __lt__ in SJFProcess
        # to compare remaining time automatically
        heapq.heappush(self.readyqueue, process)

    def is_empty(self):
        return len(self.readyqueue) == 0

    def should_preempt(self, current_process: Process, new_process: Process) -> bool:
        # compare the current process' remaining time
        # and new process' remaining time
        # return a boolean
        if not self.preemptive:
            return False
        return new_process.remaining_time < current_process.remaining_time


if __name__ == "__main__":
    scheduler = FCFS()
