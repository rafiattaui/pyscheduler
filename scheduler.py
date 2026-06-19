from dataclasses import dataclass


class Process:
    def __init__(self, pid, arrival_time, burst_time, priority):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.priority = priority
        self.state = "WAITING"  # Possible states: WAITING, RUNNING, COMPLETED


@dataclass
class CPU:
    current_process: Process = None
    status: str = "IDLE"
    started_at: int = 0
