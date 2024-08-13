"""Get stats from log file."""

import argparse
from pathlib import Path
import matplotlib.pyplot as plt
from icua.extras.analysis import (
    EventLogParser,
    plot_timestamps,
    plot_intervals,
    get_guidance_intervals,
    get_acceptable_intervals,
)

from icua.event import (
    MouseButtonEvent,
    WindowOpenEvent,
    WindowCloseEvent,
    KeyEvent,
    RenderEvent,
)

# load configuration file
parser = argparse.ArgumentParser()
parser.add_argument(
    "-d",
    "--dir",
    required=False,
    help="Path to trial directory, <dir>/<experiment.id>/<participant.id>/",
    default="./",
)
parser.add_argument(
    "-p",
    "--participant",
    required=False,
    help="ID of the participant.",
    default=None,
)
parser.add_argument(
    "-e", "--experiment", required=False, help="ID of the experiment.", default=None
)

args = parser.parse_args()

# TODO remove this is just for testing!
args.dir = "C:/Users/szonya/Documents/matbii-experiment/logs"
args.experiment = "C"
args.participant = "P00"

# path that contains the log files
path = Path(args.dir).expanduser().resolve()
if args.participant and args.experiment:
    # the the experiment path has been specified explicitly
    path = path / args.experiment / args.participant

files = {f.name: f for f in path.iterdir()}
# this context prevents config errors where paths cannot be resolved (since cwd has changed)
# config_context = dict(experiment=dict(path="./"))
# config = Configuration.from_file(files["configuration.json"], context=config_context)
event_log = files[next(filter(lambda f: f.startswith("event_log"), files.keys()))]


parser = EventLogParser()
parser.discover_event_classes("matbii")

events = list(parser.parse(event_log))


# plt.show()

# get_guidance_intervals(events)
TRACKING_COLOR = "#4363d8"
RESOURCE_MANAGEMENT_COLOR = "#3cb44b"
SYSTEM_MONITORING_COLOR = "#e6194B"

task_plot_data = {
    "tracking": {"color": TRACKING_COLOR, "ymin": 0, "ymax": 1 / 3},
    "system_monitoring": {
        "color": SYSTEM_MONITORING_COLOR,
        "ymin": 1 / 3,
        "ymax": 2 / 3,
    },
    "resource_management": {
        "color": RESOURCE_MANAGEMENT_COLOR,
        "ymin": 2 / 3,
        "ymax": 1,
    },
}
ax = None

for task, intervals in get_acceptable_intervals(events):
    color = task_plot_data[task]["color"]
    ymin = task_plot_data[task]["ymin"]
    ymax = task_plot_data[task]["ymax"]
    plot_intervals(intervals, color=color, alpha=0.3, ymin=ymin, ymax=ymax, ax=ax)
    ax = plt.gca()

for task, intervals in get_guidance_intervals(events):
    ymin = task_plot_data[task]["ymin"] * 1.05
    ymax = task_plot_data[task]["ymax"] * 0.95
    plot_intervals(intervals, color="black", alpha=0.1, ymin=ymin, ymax=ymax, ax=ax)
    ax = plt.gca()


plot_timestamps(
    events,
    WindowCloseEvent | WindowOpenEvent,
    ax=plt.gca(),
    color="red",
    linestyle="--",
)
plot_timestamps(
    events, MouseButtonEvent, ax=plt.gca(), ymin=0.0, ymax=0.1, color="lime"
)
plot_timestamps(events, KeyEvent, ax=plt.gca(), ymin=0.1, ymax=0.2, color="cyan")

plot_timestamps(events, RenderEvent, alpha=0.1, ax=plt.gca())

plt.show()
