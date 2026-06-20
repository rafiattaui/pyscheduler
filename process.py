import logging

logger = logging.getLogger(__name__)

class Process:
    def __init__(self, pid: int, arrival_time: int, burst_time: int, priority: int):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.priority = priority
        self.state: str = "WAITING"  # Possible states: WAITING, RUNNING, COMPLETED

    def __repr__(self) -> str:
        return f"Process ID: {self.pid}, AT: {self.arrival_time}, BT: {self.burst_time}, Remaining Time: {self.remaining_time}, Priority: {self.priority}, State: {self.state}"

    def reset(self):
        pass


class CPU:
    def __init__(self):
        self.process: Process = None
        self.status = "IDLE"  # IDLE , BUSY
        self.started_at: int = None

    def assign(self, process: Process, started_at: int):
        if self.status == "BUSY":
            logger.error("Unable to assign new process, CPU still busy.")
        else:
            self.process = process
            self.started_at = started_at
            self.status = "BUSY"
            logger.debug(f"T{started_at}: CPU assigned process {process.pid}")

    def release(self):
        # let go of current process
        if self.status == "BUSY":
            self.process = None
            self.status = "IDLE"
            logger.debug("process released, cpu now idle")
        else:
            logger.debug("No process to release.")
