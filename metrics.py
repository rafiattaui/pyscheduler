from process import Process


class Metrics:
    def __init__(self):
        self.execution_order: list[int] = []
        # key: process id, value: [turnaround time, waiting time]
        self.processes: dict[int, tuple[int, int]] = {}
        self.awt = 0  # average waiting time
        self.att = 0  # average turnaround time

    def add_process(self, process: Process, completed_time: int):
        turnaround_time = completed_time - process.arrival_time
        waiting_time = turnaround_time - process.burst_time

        self.processes[process.pid] = (turnaround_time, waiting_time)
        self._recalculate_att()
        self._recalculate_awt()

    def _recalculate_awt(self):
        awt = 0
        for _, waiting_time in self.processes.values():
            awt += waiting_time
        awt /= len(self.processes)
        self.awt = awt

    def _recalculate_att(self):
        att = 0
        for turnaround_time, _ in self.processes.values():
            att += turnaround_time
        att /= len(self.processes)
        self.att = att

    def __str__(self):
        lines = ["PID | Turnaround | Waiting"]
        for pid, (tt, wt) in self.processes.items():
            lines.append(f"{pid:3} | {tt:10} | {wt:7}")
        lines.append(f"\nAverage Turnaround: {self.att:.2f}")
        lines.append(f"Average Waiting:    {self.awt:.2f}")
        return "\n".join(lines)
