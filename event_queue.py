import heapq
from process import Process
import logging

logger = logging.getLogger(__name__)


class QueueEmptyError(Exception):
    pass


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
        return f"Event {self.type}, Time: {self.time}, Priority: {self.priority}, Process: {self.process}"

    def __lt__(self, other) -> bool:
        if self.time != other.time:  # compare based on time
            return self.time < other.time
        return (
            self.priority < other.priority
        )  # if time is same, compare based on priority


class EventQueue:
    def __init__(self):
        self.events = []

    def add_event(self, event: Event):
        heapq.heappush(self.events, event)

    def get_next_event(self) -> Event:
        # this will return the event with the earliest time,
        # rather than incrementing the clock and checking for events at each time step.
        if self.events:
            return heapq.heappop(self.events)
        raise QueueEmptyError("No more events in the queue.")

    def peek(self) -> Event:
        return self.events[0]

    def isEmpty(self) -> bool:
        # true if atleast one item, false if empty
        return len(self.events) == 0

    def __len__(self) -> int:
        return len(self.events)


if __name__ == "__main__":
    # tests and usage
    queue = EventQueue()
    event1 = Event("COMPLETED", 1, 0, None)
    event2 = Event("ARRIVAL", 1, 1, None)
    event3 = Event("ARRIVAL", 5, 0, None)

    events = [event1, event2, event3]
    for event in events:
        queue.add_event(event)

    print(queue.events)

    for __ in events:
        event = queue.get_next_event()
        print(event)
