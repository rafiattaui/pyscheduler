from event_queue import EventQueue, Event
from scheduler import FCFS
from process import Process, CPU
from metrics import Metrics
import logging

logging.basicConfig(level=logging.DEBUG, format="[%(name)s] %(message)s")

logger = logging.getLogger(__name__)


class Program:
    def __init__(self):
        self.is_running = False
        self.event_queue = EventQueue()
        self.clock = 0
        self.cpu = CPU()
        self.scheduler = FCFS()
        self.metrics = Metrics()

    def run(self):
        self.is_running = True
        while self.is_running:
            status = self._poll_event()
            if status == 0:
                self.is_running = False

    def _poll_event(self):
        if not self.event_queue.isEmpty():
            event = self.event_queue.get_next_event()
            if not event.valid:
                return 1
            self.clock = event.time
            logger.debug(f"T{self.clock}: event polled, {event}")
            match event.type:
                case "ARRIVAL":
                    self._handle_arrival(event)
                    return 1
                case "COMPLETION":
                    self._handle_completion(event)
                    return 1
                case "SCHEDULE":
                    self._handle_schedule(event)
                    return 1
                case _:
                    logger.debug("T{self.clock}: Unknown event type polled.")
                    return 0
        return 0

    def _handle_arrival(self, event: Event):
        # a new process arrives, add it to the scheduler's ready queue
        self.scheduler.add_process(event.process)
        logger.debug(f"T{self.clock}: process arrived: {event.process}")
        logger.debug(f"T{self.clock}: ready queue: {self.scheduler.readyqueue}")

        status = self.cpu.status
        logger.debug(f"T{self.clock}: cpu is {status}")
        if status == "IDLE":
            # if the cpu is idle, enqueue a schedule event at the current time
            # so it is automatically inserted to the CPU after this arrival event
            self.event_queue.add_event(
                Event(
                    "SCHEDULE",
                    self.clock,
                    1,
                    None,  # it will take the process from the scheduler
                )
            )

    def _handle_completion(self, event: Event):
        # release the current process from the cpu
        completed_process = self.cpu.process
        self.cpu.release()
        logger.debug(
            f"T{self.clock}: process {event.process.pid} completed at time {self.clock}"
        )
        logger.debug(f"T{self.clock}: cpu now idle")
        # record metrics here

        # check if ready queue empty
        # if ready queue has a process
        if not self.scheduler.is_empty():
            logger.debug(f"T{self.clock}: found process in ready_queue")
            logger.debug(f"T{self.clock}: new schedule event enqueued for next process")
            self.event_queue.add_event(Event("SCHEDULE", self.clock, 1, None))

    def _handle_schedule(self, event: Event):
        # pops the ready queue
        process = self.scheduler.select_next()
        self.cpu.assign(process, self.clock)

        completion = Event(
            "COMPLETION",
            self.clock + process.remaining_time,  # finish time
            0,  # priority
            process,  # carry process for metrics
        )

        self.cpu.process_completion_event = completion
        self.event_queue.add_event(completion)

    def load_processes(self, processes: list[Process]):
        for process in processes:
            self.event_queue.add_event(
                Event("ARRIVAL", process.arrival_time, 0, process)
            )


def main():
    process1 = Process(1, 1, 3, 1)
    process2 = Process(2, 4, 2, 1)
    process3 = Process(3, 7, 1, 1)

    processes = [process1, process2, process3]

    program = Program()
    program.load_processes(processes)

    program.run()


if __name__ == "__main__":
    main()
