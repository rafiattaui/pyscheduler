class Process:
    def __init__(self, pid: int, arrival_time: int, burst_time: int, priority: int):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.priority = priority
        self.state: str = "WAITING"  # Possible states: WAITING, RUNNING, COMPLETED

    def __repr__(self) -> str:
        return f"Process ID: {self.PID}, AT: {self.arrival_time}, BT: {self.burst_time}, Remaining Time: {self.remaining_time}, Priority: {self.priority}, State: {self.state}"

    def reset(self):
        pass

class CPU:
    def __init__(self):
        self.process: Process = None
        self.status = "IDLE"
        self.started_at: int = None;