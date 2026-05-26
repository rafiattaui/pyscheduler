from dataclasses import dataclass

@dataclass
class Process:
    pid: int
    arrival_time: float
    burst_time: float
    priority: int