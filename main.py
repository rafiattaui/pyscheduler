from event_queue import EventQueue, Event


class Program:
    def __init__(self):
        self.is_running = False
        self.event_queue = EventQueue()
        self.clock = 0
        self.cpu = None
        self.scheduler = None
        self.metrics = None
        self.handlers = {
            "ARRIVAL": None,
            "COMPLETION": None,
            "SCHEDULE": None,
        }

    def run(self):
        while self.is_running:
            pass


def main():
    program = Program()
    program.run()


if __name__ == "__main__":
    main()
