"""Example script that will parse a raw matbii log file and extract events of a specific type."""

import argparse
from pathlib import Path
from icua.extras.analysis import (
    EventLogParser,
    get_mouse_motion_events,
    get_attention_intervals,
)

# load configuration file
parser = argparse.ArgumentParser()
parser.add_argument(
    "-p",
    "--path",
    required=False,
    help="Path to trial directory, typically: .../<experiment.id>/<participant.id>/",
    default=Path(__file__).parent
    / "example_logs/example-system-monitoring-only/",  # default example log file
)

args = parser.parse_args()

# this parser will be used to parse event log files
parser = EventLogParser()
# gather all the event types present in matbii and ensure they are loaded properly before parsing
parser.discover_event_classes("matbii")
# locate the log file in an experiment directory (if it is known you might skip this step)
log_file_path = parser.get_event_log_file(args.path)
# this parses the log file and produces a list of events (in order of the file)
events = list(parser.parse(log_file_path))

# Attention via mouse motion
df = get_mouse_motion_events(parser, events)
# This will get the intervals that show which task the user was attending and when
# The same function can be used for other attendence conditions - e.g. eyetracking, or user interaction, only the "target" columns is required.
attention_intervals = dict(get_attention_intervals(df))["system_monitoring"]
print(attention_intervals)
