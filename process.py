import logging
import random


logger = logging.getLogger(__name__)


class Process:
    def __init__(self, pid: int, arrival_time: int, burst_time: int, priority: int):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.priority = priority

    def __repr__(self) -> str:
        return f"[P{self.pid}] AT={self.arrival_time} BT={self.burst_time} RT={self.remaining_time} PRI={self.priority}"

    def __lt__(self, other: "Process"):
        # compare based on remaining_time
        return self.remaining_time < other.remaining_time

    def reset(self):
        pass


class CPU:
    def __init__(self):
        self.process: Process = None
        self.status = "IDLE"  # IDLE , BUSY
        self.started_at: int = None
        self.process_completion_event: "Event" = None

    def assign(self, process: Process, started_at: int):
        if self.status == "BUSY":
            logger.error("Unable to assign new process, CPU still busy.")
        else:
            self.process = process
            self.started_at = started_at
            self.status = "BUSY"
            logger.debug(f"T{started_at}: CPU assigned process {process.pid}")

    def release(self):
        # for processes that have finished
        if self.status == "BUSY":
            self.process = None
            self.process_completion_event = None
            self.status = "IDLE"
            logger.debug("process released, cpu now idle")
        else:
            logger.debug("No process to release.")

    def preempt(self, time: int) -> Process:
        # calculate how much time the process ran
        time_ran = time - self.started_at
        self.process.remaining_time -= time_ran
        logger.debug(f"T{time}: preemptively stopping process {self.process.pid} with remaining time: {self.process.remaining_time}")
        # invalidate the old completion event,
        # a new completion event will be created via handle_schedule
        self.process_completion_event.valid = False
        self.process_completion_event = None
        process = self.process
        self.process = None
        self.status = "IDLE"

        return process

def generate_processes(n: int, max_arrival: int = 10, max_burst: int = 10, max_priority: int = 5) -> list[Process]:
    processes = []
    for i in range(1, n + 1):
        arrival  = random.randint(0, max_arrival)
        burst    = random.randint(1, max_burst)
        priority = random.randint(0, max_priority)
        processes.append(Process(i, arrival, burst, priority))
    return processes