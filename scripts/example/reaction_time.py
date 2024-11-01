"""Example script to calculate reaction times from a log file."""

import argparse
from pathlib import Path
from matbii.extras.analysis import (
    EventLogParser,
    get_system_monitoring_task_events,
    get_acceptable_intervals,
)


# path as command line argument
argparser = argparse.ArgumentParser()
argparser.add_argument(
    "-p",
    "--path",
    required=False,
    help="Path to event log file, typically: .../<experiment.id>/<participant.id>/event_log_*.log",
    default=Path(__file__).parent
    / "example_logs/system_monitoring.log",  # default example log file
)
args = argparser.parse_args()
parser = EventLogParser()
parser.discover_event_classes("matbii")
events = list(parser.parse(args.path))

# To compute the reaction time for a task, we need:
# 1. when the tasks was in acceptable/unacceptable state
# 2. when the mouse or keyboard was pressed for the given task

# We will do this for the system monitoring task here.

# 1. Get when the task was in an acceptable state
acceptable_intervals = dict(get_acceptable_intervals(events))["system_monitoring"]
# `acceptable_intervals` contains N pairs (t1, t2) which are logging timestamps recording when the guidance agent judged the task to be acceptable.

# 2. Get the relevant task data
df = get_system_monitoring_task_events(events)
# `df` is a pandas DataFrame that contains a running update of the state of the task (one entry each time the task state was changed).

# For each entry of `df` we want to know if the task was in an acceptable state - according to the guidance agent.
# NOTE: There may be small discrepencies in whether the state was actually (according to its state).
# This is because the guidance agent is working from observations, which may be outdated if an update happens after it has observed.
# This has very little practical impact on the reaction time computation (the difference will only be a single frame, so ~10ms, much faster than a human can meaningfully react to any kind of guidance.)
