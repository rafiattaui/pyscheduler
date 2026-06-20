from process import Process
import plotly.express as px
import pandas as pd

class Metrics:
    def __init__(self):
        self.segments: list[tuple[int,int,int]] = [] # list of (pid, start, end)
        # key: process id, value: [turnaround time, waiting time]
        self.processes: dict[int, tuple[int, int]] = {}
        self._current_start = {}
        self._priorities: dict[int, int] = {}  # pid -> priority, for chart labeling
        self.awt = 0  # average waiting time
        self.att = 0  # average turnaround time

    def add_process(self, process: Process, completed_time: int):
        turnaround_time = completed_time - process.arrival_time
        waiting_time = turnaround_time - process.burst_time

        self.processes[process.pid] = (turnaround_time, waiting_time)
        self._priorities[process.pid] = process.priority
        self._recalculate_att()
        self._recalculate_awt()

    def record_start(self, process, time):
        self._current_start[process.pid] = time
        self._priorities[process.pid] = process.priority

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

    def plot_gantt(self, title: str = "CPU Scheduling Gantt Chart", color_map: dict[str, str] | None = None):
        rows = []
        for pid, start, end in self.segments:
            rows.append({
                "Process": f"P{pid}",
                "Start": start,
                "Finish": end,
                # Duration drives the bar's geometry (length); px.bar needs a
                # length value paired with `base`, not an absolute time, or
                # the bar would be drawn far too long. Finish is what we show
                # to the user instead, since "where does this end" is more
                # readable than "how long is this".
                "Duration": end - start,
                "Priority": self._priorities.get(pid),
            })

        df = pd.DataFrame(rows)

        fig = px.bar(
            df,
            x="Duration",
            y="Process",
            base="Start",
            color="Process",
            color_discrete_map=color_map,
            title=title,
            orientation="h",
            text="Finish",
            hover_data={"Start": True, "Finish": True, "Priority": True, "Duration": False},
        )

        fig.update_traces(texttemplate="t=%{text}", textposition="inside")

        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Process",
            xaxis=dict(tick0=0, dtick=1)
        )

        fig.show()


def build_process_color_map(pids: list[int]) -> dict[str, str]:
    """Builds a fixed 'P{pid}' -> color mapping from a palette, keyed by a
    stable (sorted) pid order. Pass the SAME list of pids (e.g. from the
    original, un-deep-copied process list used across a comparison run) to
    every plot_gantt() call so a given process gets the same color in every
    algorithm's chart, instead of px.bar re-assigning colors per-chart based
    on each run's own (different) first-appearance order."""
    palette = px.colors.qualitative.Plotly
    unique_pids = sorted(set(pids))
    return {f"P{pid}": palette[i % len(palette)] for i, pid in enumerate(unique_pids)}


def plot_comparison(results: dict[str, "Metrics"]):
    """Bar chart comparing average turnaround / waiting time across multiple
    scheduler runs. `results` maps an algorithm name (e.g. 'fcfs') to its
    Metrics instance after a completed run."""
    rows = []
    for name, metrics in results.items():
        rows.append({"Algorithm": name.upper(), "Metric": "Avg Turnaround", "Value": metrics.att})
        rows.append({"Algorithm": name.upper(), "Metric": "Avg Waiting", "Value": metrics.awt})

    df = pd.DataFrame(rows)

    fig = px.bar(
        df,
        x="Algorithm",
        y="Value",
        color="Metric",
        barmode="group",
        title="Scheduler Comparison: Avg Turnaround vs Avg Waiting Time",
        text_auto=".2f",
    )

    fig.update_layout(
        xaxis_title="Scheduling Algorithm",
        yaxis_title="Time",
    )

    fig.show()