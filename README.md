# PyScheduler
A python program simulating CPU scheduling algorithms, utilizing Event Loop architecture and OOP.

## How it Works
The main loop starts within program.py. A class Program is initialized containing an event queue, a CPU, and a scheduler.

### Program
Program is responsible for connecting all the different layers (EventQueue, CPU, Scheduler) under one program, advances the loop and does operations based on the event polled from the event queue each tick.

```py
def __init__(self, scheduler=RoundRobin(2)):
        self.is_running = False
        self.event_queue = EventQueue()
        self.clock = 0
        self.cpu = CPU()
        self.scheduler = scheduler
        self.metrics = Metrics()
```

The simulation skips to ticks with significant events occuring, it does not simulate empty ticks (such as when no processes arrive, and the CPU continues to work on its already assigned process).

```py
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
```

When a new process arrives, the ``Program`` creates a new event to schedule a ``Process`` insertion to the ``CPU`` if the ``CPU`` is idle at the same tick.

```py
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
```

When a new process is being inserted to the ``CPU``, the ``Program`` also creates a new ``Event`` of type ``COMPLETION`` that when the Program polls and retrieves, will end the ``CPU``'s work with that process.

```py
completion = Event(
            "COMPLETION",
            self.clock + process.remaining_time,  # finish time
            -1,  # priority: must run before any same-tick ARRIVAL (priority 0).
                 # Otherwise a process finishing exactly this tick could be
                 # incorrectly "preempted" by an arrival processed first,
                 # leaving it stuck in the ready queue with remaining_time=0.
            process, 
        )
```

Round-Robin time slices work by simply scheduling a time slice based on the time quantum set, and for each process scheduled to enter the ``CPU``, a ``TIME_SLICE_EXPIRED Event`` is also pushed to the queue. When the program retrieves that event, it simply tells the ``CPU`` to preempt the current process, invalidate its original ``COMPLETION event`` and then the ``Program`` pushes a new ``SCHEDULE Event`` telling the ``CPU`` to retrieve a new process.

```py
def _handle_time_slice_expired(self, event: Event):
        # when time slice expires, the cpu will preemptively stop the process,
        # the previous completion event will be invalidated, and a new one will be made
        process = self.cpu.preempt(self.clock)
        self.metrics.record_end(process, self.clock)
        self.scheduler.add_process(process)
        self.event_queue.add_event(Event("SCHEDULE", self.clock, 1, None))
```

### Event Queue
The event queue is responsible for handling events such as process completions, interrupts, and process arrivals.

The decoupling of the logic of process arrivals allows the ``Program`` to react only when something actually changes — an arrival, a completion, a scheduling decision, or a time-slice expiry — rather than stepping through every unit of time. This keeps the simulation efficient even for large arrival/burst times, since idle gaps where nothing happens are never visited.

Each ``Event`` carries a type, the tick it should fire at, a priority (used to break ties when multiple events land on the same tick), and an optional reference to the Process it concerns:

```py
class Event:

    def __init__(
        self, event_type: str, time: int, priority: int, process: Process | None
    ):
        self.type = event_type
        self.time = time
        self.priority = priority
        self.process = process
        self.valid: bool = True

    def __repr__(self) -> str:
        return f"[{self.type}] T={self.time} PRI={self.priority} P={self.process.pid if self.process else None}"

    def __lt__(self, other) -> bool:
        if self.time != other.time:  # compare based on time
            return self.time < other.time
        return (
            self.priority < other.priority
        )  # if time is same, compare based on priority
```

``EventQueue`` wraps a heapq list of ``Event``s, always returning an event with the earliest time and lowest priority.

```py
class EventQueue:
    def __init__(self):
        self.events = []

    def add_event(self, event):
        heapq.heappush(self.events, event)

    def get_next_event(self):
        if self.events:
            return heapq.heappop(self.events)
        raise QueueEmptyError("No more events in the queue.")
```

Priority ordering matters here because multiple processes can arrive at the same tick, a process finishing and a new one arriving at the same instant, for example. The order they're processed in changes the outcome. ```COMPLETION``` events are given the highest priority (processed first), so a process that's finishing this tick is always finalized before any same-tick ```ARRIVAL``` gets a chance to evaluate preemption against it. ARRIVAL and ```COMPLETION``` are processed before ```SCHEDULE/TIME_SLICE_EXPIRED```, so the ready queue reflects every same-tick change in process state before a scheduling decision is made from it.

```py
self.event_queue.add_event(
    Event("SCHEDULE",self.clock,1,None,)
    )
```

If a process is to be preemptively stopped, a new ``COMPLETION Event`` would have to be pushed to the event queue, and the old one would need to be invalidated. Because the ``EventQueue`` uses a ``Min-Heap``, finding the correct event would not be efficient therefore the CPU maintains a pointer to process' completion event and invalidates it.
When the program polls for an event, it checks if the event is valid or not.

```py
event = self.event_queue.get_next_event()
            if not event.valid:
                return 1
```

### Process and CPU
In ``process.py``, a class ``Process`` stores its arrival time, burst time, remaining time, and priority (for priority scheduling).

```py
class Process:
    def __init__(self, pid: int, arrival_time: int, burst_time: int, priority: int):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.priority = priority
```

A ``CPU`` stores the currently assigned ``process``, its ``COMPLETION Event``, and the status of the ``CPU``.

```py
def __init__(self):
        self.process: Process = None
        self.status = "IDLE"  # IDLE , BUSY
        self.started_at: int = None
        self.process_completion_event: "Event" = None
```

It contains several methods used to assign, release, and pre-emptively stop.

```py
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
```

## Design Practices Applied
### Strategy Pattern
Each scheduler algorithm inherits from a abstract base class ``BaseScheduler``, this contains abstract methods which each scheduler must implement.

```py
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

    @abstractmethod
    def get_time_slice_event(self, process: Process, clock: int) -> "Event | None":
        pass
```

By seperating the logic from the ``Program`` and the ``Scheduler``, we maintain a cohesive event loop within ``Program`` such that we do not need to code special if-else cases for specific algorithms and their operations. ``Program`` only cares about what the scheduler returns, not how it returns it.

### Single Responsibility
Each module owns exactly one concern: ``EventQueue`` only orders/serves events, ``CPU`` only tracks what's running and for how long, Process is a pure data holder, the ``Scheduler`` classes only decide what's next. ``Program`` is the only thing that knows how to wire all of them together. None of these classes reach into each other's underlying logic. ``Program`` mediates everything.

### Discrete Event Simulation
The whole engine is built around "jumping to the next meaningful tick" rather than stepping through every unit of time, ``EventQueue`` is the priority queue driving that; ``_poll_event`` is the engine's step function.
```py
if not self.event_queue.isEmpty():
            event = self.event_queue.get_next_event()
            if not event.valid:
                return 1
            self.clock = event.time
            logger.debug(f"T{self.clock}: event polled, {event}")
```

## How to Run
```bash
git clone https://github.com/rafiattaui/pyscheduler
cd /pyscheduler
```
Clone the repository, and move inside the directory.

```bash
uv sync 
```
Use UV to install any dependencies.

```bash
uv run python program.py
```
Run the program.