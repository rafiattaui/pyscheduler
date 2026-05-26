from abc import ABC, abstractmethod
from process import Process
from sortedcontainers import sortedlist

class BaseSchedulingAlgorithm(ABC):
    processes: list[Process]
    
    def __init__(self, processes: list[Process]):
        self.processes = processes
    
    @abstractmethod
    def tick(self):
        # define the loop here
        pass
        
class FirstComeFirstServe(BaseSchedulingAlgorithm):
    
    def tick(self) -> int:
        
    
class ShortestJobFirst(BaseSchedulingAlgorithm):
    
    def tick(self):
        pass
    
class RoundRobin(BaseSchedulingAlgorithm):
    
    def tick(self):
        pass
    
class PriorityScheduling(BaseSchedulingAlgorithm):
    
    def tick(self):
        pass
    
if __name__ == "__main__":
    x = Process(
        pid= 2,
        arrival_time=3,
        burst_time=5,
        priority=1
    )

    y = Process(
        pid= 1,
        arrival_time=0,
        burst_time=2,
        priority=0
    )

    z = Process(
        pid=3,
        arrival_time=2,
        burst_time=4,
        priority=2
    )
    
    status = 0
    algo = FirstComeFirstServe([x, y, z])
    
    while (status == 0):
        status = algo.tick()
    