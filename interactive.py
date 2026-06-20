"""
An interactive GUI app for pyscheduler
"""
from textual import on
from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Label, Select, Collapsible, Button, Input
from textual.containers import Vertical, HorizontalGroup, Horizontal
from process import Process
from scheduler import FCFS, SJF, RoundRobin
import logging

process1 = Process(1, 1, 2, 0)

PROCESSES = [
    process1
]

SCHEDULER = ""

SCHEDULERS = [
    ("First Come First Serve", "fcfs"),
    ("Shortest Job First", "sjf"),
    ("Shortest Job First (Pre-Emptive)", "sjf-pe"),
    ("Round Robin", "rr"),
]

SCHEDULER_MAP = {
    "fcfs": FCFS(),
    "sjf": SJF(preemptive=False),
    "sjf-pe": SJF(preemptive=True),
    "rr": RoundRobin(quantum=2),
}

class TextualLogHandler(logging.Handler):
    def __init__(self, log_widget: RichLog):
        super().__init__()
        self._log = log_widget

    def emit(self, record: logging.LogRecord):
        self._log.write(self.format(record))

class LabeledSelect(Vertical):
    DEFAULT_CSS = """
    LabeledSelect {
    width: 90%;
    height: auto;
    margin-bottom: 1;
    margin-top: 1;
    padding: 1 1;
    background: $panel;
    }

    LabeledSelect Label {
    color: $text;
    padding-bottom: 1;
    }
    """

    def __init__(self, label: str, options: list[tuple[str, str]], id: str):
        super().__init__()
        self._label = label
        self._options = options
        self._select_id = id

    def compose(self) -> ComposeResult:
        yield Label(self._label)
        yield Select(self._options, id=self._select_id)

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed):
        SCHEDULER = str(event.value)
        self.notify(f"Scheduler: {SCHEDULER}", severity="information")

class CollapsibleProcess(Collapsible):
    def __init__(self, process: Process):
        super().__init__(title=f"P{process.pid}", collapsed=True)
        self._process = process

    def compose(self) -> ComposeResult:
        yield Label(f"Arrival Time:  {self._process.arrival_time}")
        yield Label(f"Burst Time:    {self._process.burst_time}")
        yield Label(f"Priority:      {self._process.priority}")

class ProcessListContainer(Vertical):
    DEFAULT_CSS = """
    ProcessListContainer {
    background: $panel;
    width: 90%;
    padding: 1 1;
    }
    
    #process-list-label {
    text-style: bold;
    margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("List of Processes", id="process-list-label")
        for process in PROCESSES:
            with Collapsible(title=f"P{process.pid}", collapsed=True):
                yield Label(f"Arrival Time:  {process.arrival_time}")
                yield Label(f"Burst Time:    {process.burst_time}")
                yield Label(f"Priority:      {process.priority}")

class AddProcessModal(ModalScreen):
    DEFAULT_CSS = """
        AddProcessModal {
        align: center middle;
        }

        #modal-container {
        width: 40%;
        height: auto;
        max-height: 60%;
        background: $panel;
        padding: 1 2;
        }

        #modal-container Label {
            text-style: bold;
            margin-bottom: 1;
            color: $text;
        }

        #modal-container Input {
        margin: 1 0;
        height: auto;
        }

        #modal-container Horizontal {
        
        }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id='modal-container'):
            yield Label("Add Process")
            yield Input(placeholder="Process ID", id="pid-field", type="number")
            yield Input(placeholder="Arrival Time", id="at-field", type="number")
            yield Input(placeholder="Burst Time", id="bt-field", type="number")
            yield Input(placeholder="Priority", id="priority-field", type="number")
            with HorizontalGroup():
                yield Button("Close", id="close-btn", variant="error")
                yield Button("Add", id="add-btn", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-btn":
            self.app.pop_screen()
        elif event.button.id == "add-btn":
            try:
                pid      = int(self.query_one("#pid-field", Input).value)
                at       = int(self.query_one("#at-field", Input).value)
                bt       = int(self.query_one("#bt-field", Input).value)
                priority = int(self.query_one("#priority-field", Input).value)

                process = Process(pid, at, bt, priority)
                self.dismiss(process)  # passes the process back to the caller
            except:
                self.notify("All fields must be filled in.", severity="error")

class ProgramContainer():
    pass

class PySchedulerApp(App):
    TITLE = "PyScheduler by rafiattaui"
    CSS_PATH = "interactive.tcss"
    def __init__(self):
        super().__init__()
        self.theme = "tokyo-night"

    def compose(self) -> ComposeResult:
        # Create child widgets
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield LabeledSelect(
                    label="Scheduler",
                    options=SCHEDULERS,
                    id="scheduler-select"
                )
                yield ProcessListContainer()
                yield Button("+ Add Process", id="add-process-btn")
            with Vertical(id="program"):
                yield Label("Simulation Log", id="log-label")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add-process-btn":
            self.push_screen(AddProcessModal(), self.handle_new_process)

    def handle_new_process(self, process: Process):
        if process:
            PROCESSES.append(process)
            self.notify(f"Added P{process.pid}")
            container = self.query_one("ProcessListContainer")
            container.refresh(recompose=True)

if __name__ == "__main__":
    app = PySchedulerApp()
    app.run()