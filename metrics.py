from process import Process
import plotly.express as px
import pandas as pd

class Metrics:
    def __init__(self):
        self.segments: list[tuple[int,int,int]] = [] # list of (pid, start, end)
        # key: process id, value: [turnaround time, waiting time]
        self.processes: dict[int, tuple[int, int]] = {}
        self._current_start = {}
        self.awt = 0  # average waiting time
        self.att = 0  # average turnaround time

    def add_process(self, process: Process, completed_time: int):
        turnaround_time = completed_time - process.arrival_time
        waiting_time = turnaround_time - process.burst_time

        self.processes[process.pid] = (turnaround_time, waiting_time)
        self._recalculate_att()
        self._recalculate_awt()

    def record_start(self, process, time):
        self._current_start[process.pid] = time

    def record_end(self, process, time):
        start = self._current_start.pop(process.pid, None)
        if start is not None:
            self.segments.append((process.pid, start, time))

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
        lines.append("\nExecution Segments:")
        for pid, start, end in self.segments:
            lines.append(f"  P{pid}: t={start} → t={end} (duration={end - start})")
        return "\n".join(lines)
    
    def plot_gantt(self):
        rows = []
        for pid, start, end in self.segments:
            rows.append({
                "Process": f"P{pid}",
                "Start": start,
                "Duration": end - start
            })

        df = pd.DataFrame(rows)

        fig = px.bar(
            df,
            x="Duration",
            y="Process",
            base="Start",
            color="Process",
            title="CPU Scheduling Gantt Chart",
            orientation="h"
        )

        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Process",
            xaxis=dict(tick0=0, dtick=1)
        )

        fig.show()
