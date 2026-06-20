import copy
import logging
from typing import Callable

from event_queue import EventQueue, Event
from scheduler import BaseScheduler, FCFS, SJF, RoundRobin, PriorityScheduler
from process import Process, CPU, generate_processes
from metrics import Metrics, plot_comparison

logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")

logger = logging.getLogger(__name__)

AVAILABLE_SCHEDULERS = ["fcfs", "sjf", "sjf-pe", "rr", "priority", "priority-pe"]


class Program:
    def __init__(self, scheduler=RoundRobin(2)):
        self.is_running = False
        self.event_queue = EventQueue()
        self.clock = 0
        self.cpu = CPU()
        self.scheduler = scheduler
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
                case "TIME_SLICE_EXPIRED":
                    self._handle_time_slice_expired(event)
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
        elif status == "BUSY":
            if self.scheduler.should_preempt(self.cpu.process, event.process):
                # if true,
                # release the current process
                # and a create new event to schedule the process
                # at the same time
                process = self.cpu.preempt(self.clock)
                self.metrics.record_end(process, self.clock)
                self.scheduler.add_process(process)
                self.event_queue.add_event(Event("SCHEDULE", self.clock, 1, None))

    def _handle_completion(self, event: Event):
        # release the current process from the cpu
        completed_process = self.cpu.process
        self.cpu.release()
        logger.debug(
            f"T{self.clock}: process {event.process.pid} completed at time {self.clock}"
        )
        logger.debug(f"T{self.clock}: cpu now idle")
        # record metrics here

        self.metrics.add_process(completed_process, self.clock)
        self.metrics.record_end(completed_process, self.clock)

        # check if ready queue empty
        # if ready queue has a process
        if not self.scheduler.is_empty():
            logger.debug(f"T{self.clock}: found process in ready_queue")
            logger.debug(f"T{self.clock}: new schedule event enqueued for next process")
            self.event_queue.add_event(Event("SCHEDULE", self.clock, 1, None))

    def _handle_schedule(self, event: Event):
        # Guard against duplicate SCHEDULE events. These can be queued more than
        # once at the same clock tick when multiple preemption-triggering events
        # (e.g. two arrivals) land at the same timestamp: the first event preempts
        # the CPU (which flips it back to IDLE) and queues a SCHEDULE event, then a
        # second event at the same tick sees that still-IDLE status (the first
        # SCHEDULE event hasn't run yet) and queues another one. If we acted on
        # this duplicate, it would pop a process from the ready queue without
        # actually being able to place it in the CPU and corrupt
        # cpu.process_completion_event, eventually causing a crash when that
        # bogus completion event fires. Safe to no-op here: the process stays in
        # the ready queue and will be picked up by the next legitimate schedule.
        if self.cpu.status == "BUSY":
            logger.debug(f"T{self.clock}: duplicate SCHEDULE event ignored, cpu already busy")
            return

        # pops the ready queue
        process = self.scheduler.select_next()
        self.cpu.assign(process, self.clock)
        self.metrics.record_start(process, self.clock)

        # check if scheduler uses time slices
        # if it does, it will return a time_slice event that we can queue to the event queue
        time_slice = self.scheduler.get_time_slice_event(process, self.clock)
        if time_slice:
            self.event_queue.add_event(time_slice)

        completion = Event(
            "COMPLETION",
            self.clock + process.remaining_time,  # finish time
            0,  # priority
            process,  # carry process for metrics
        )

        self.cpu.process_completion_event = completion
        self.event_queue.add_event(completion)

    def _handle_time_slice_expired(self, event: Event):
        # when time slice expires, the cpu will preemptively stop the process,
        # the previous completion event will be invalidated, and a new one will be made
        process = self.cpu.preempt(self.clock)
        self.metrics.record_end(process, self.clock)
        self.scheduler.add_process(process)
        self.event_queue.add_event(Event("SCHEDULE", self.clock, 1, None))

    def load_processes(self, processes: list[Process]):
        for process in processes:
            self.event_queue.add_event(
                Event("ARRIVAL", process.arrival_time, 0, process)
            )


def make_scheduler_factory(name: str, quantum: int | None = None) -> Callable[[], BaseScheduler]:
    """Returns a zero-arg callable that builds a *fresh* scheduler instance
    for the given algorithm name. A fresh instance per run is required since
    schedulers carry their own readyqueue state."""
    if name == "fcfs":
        return lambda: FCFS()
    elif name == "sjf":
        return lambda: SJF(preemptive=False)
    elif name == "sjf-pe":
        return lambda: SJF(preemptive=True)
    elif name == "rr":
        if quantum is None:
            raise ValueError("Round Robin requires a quantum.")
        return lambda: RoundRobin(quantum=quantum)
    elif name == "priority":
        return lambda: PriorityScheduler(preemptive=False)
    elif name == "priority-pe":
        return lambda: PriorityScheduler(preemptive=True)
    else:
        raise ValueError(f"Unknown scheduler: {name}")


def collect_processes() -> list[Process]:
    """Shared process-input flow for both single and comparison modes."""
    processes: list[Process] = []
    mode = input("Mode (manual / random): ").strip().lower()

    if mode == "random":
        n = int(input("Number of processes: "))
        processes = generate_processes(n)
        for p in processes:
            print(f"  P{p.pid} AT={p.arrival_time} BT={p.burst_time} PRI={p.priority}")
    else:
        print("\nAdd processes (leave PID blank to stop):")
        while True:
            pid_input = input("PID: ").strip()
            if not pid_input:
                break
            try:
                pid      = int(pid_input)
                at       = int(input("Arrival Time: "))
                bt       = int(input("Burst Time: "))
                priority = int(input("Priority: "))
                processes.append(Process(pid, at, bt, priority))
                print(f"Added P{pid}\n")
            except ValueError:
                print("Invalid input, try again.\n")

        if not processes:
            print("No processes added.")
            return []

    return processes


def run_single(scheduler: BaseScheduler, processes: list[Process]) -> tuple[Program, Metrics]:
    """Runs one isolated simulation. Always deep-copies the incoming
    processes so the caller's original list (e.g. the shared baseline used
    across multiple comparison runs) is never mutated."""
    isolated_processes = copy.deepcopy(processes)
    program = Program(scheduler=scheduler)
    program.load_processes(isolated_processes)
    program.run()
    return program, program.metrics


def run_comparison(
    processes: list[Process],
    scheduler_factories: dict[str, Callable[[], BaseScheduler]],
) -> dict[str, Metrics]:
    """Runs every selected algorithm against an identical starting set of
    processes. Each run gets its own deep-copied processes and a brand new
    scheduler/Program instance, so results never bleed into one another."""
    results: dict[str, Metrics] = {}
    for name, factory in scheduler_factories.items():
        scheduler = factory()
        _, metrics = run_single(scheduler, processes)
        results[name] = metrics
        print(f"\n--- {name.upper()} ---")
        print(metrics)
    return results


def print_comparison_table(results: dict[str, Metrics]):
    print("\n=== Comparison Results ===")
    header = f"{'Algorithm':<10} | {'Avg Turnaround':>15} | {'Avg Waiting':>12}"
    print(header)
    print("-" * len(header))
    for name, metrics in results.items():
        print(f"{name:<10} | {metrics.att:>15.2f} | {metrics.awt:>12.2f}")

    best_att = min(results.items(), key=lambda kv: kv[1].att)
    best_awt = min(results.items(), key=lambda kv: kv[1].awt)
    print(f"\nBest Avg Turnaround: {best_att[0]} ({best_att[1].att:.2f})")
    print(f"Best Avg Waiting:    {best_awt[0]} ({best_awt[1].awt:.2f})")


def run_compare_flow():
    print(f"Schedulers: {', '.join(AVAILABLE_SCHEDULERS)}")
    selection = input("Select schedulers to compare (comma separated, or 'all'): ").strip().lower()

    if selection == "all":
        chosen = AVAILABLE_SCHEDULERS[:]
    else:
        chosen = [s.strip() for s in selection.split(",") if s.strip() in AVAILABLE_SCHEDULERS]

    if not chosen:
        print("No valid schedulers selected.")
        return

    quantum = None
    if "rr" in chosen:
        quantum = int(input("Quantum for Round Robin: "))

    factories = {name: make_scheduler_factory(name, quantum) for name in chosen}

    processes = collect_processes()
    if not processes:
        return

    results = run_comparison(processes, factories)
    print_comparison_table(results)

    if input("\nShow gantt chart for each scheduler? (y/n): ").strip().lower() == "y":
        for name, metrics in results.items():
            metrics.plot_gantt(title=f"Gantt Chart - {name.upper()}")

    if input("Show side-by-side comparison chart? (y/n): ").strip().lower() == "y":
        plot_comparison(results)


def run_single_flow():
    print("Schedulers: fcfs, sjf, sjf-pe, rr, priority, priority-pe")
    scheduler_input = input("Select scheduler: ").strip().lower()

    scheduler_map = {
        "fcfs": FCFS(),
        "sjf": SJF(preemptive=False),
        "sjf-pe": SJF(preemptive=True),
        "rr": RoundRobin(quantum=int(input("Quantum: "))) if scheduler_input == "rr" else None,
        "priority": PriorityScheduler(preemptive=False),
        "priority-pe": PriorityScheduler(preemptive=True),
    }

    scheduler = scheduler_map.get(scheduler_input)
    if not scheduler:
        print("Invalid scheduler.")
        return

    processes = collect_processes()
    if not processes:
        return

    program = Program(scheduler=scheduler)
    program.load_processes(processes)

    program.run()
    print(program.scheduler)
    print(program.metrics)
    program.metrics.plot_gantt()


def main():
    print("=== PyScheduler ===")
    top_mode = input("Mode (single / compare): ").strip().lower()

    if top_mode == "compare":
        run_compare_flow()
    else:
        run_single_flow()


if __name__ == "__main__":
    main()