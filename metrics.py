class Metrics():
    def __init__(self):
        self.execution_order: list[int] = None
        # key: process id, value: [waiting time, turnaround time]
        self.processes: dict[int, tuple[int,int]] = None
        self.awt = 0 # average waiting time
        self.att = 0 # average turnaround time

    def add_process(self):
        pass

    def _recalculate_awt(self):
        pass

    def _recalculate_awt(self):
        pass

    def __str__(self):
        pass