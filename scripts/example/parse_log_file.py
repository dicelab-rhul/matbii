"""Example script that will parse a raw matbii log file and extract events of a specific type."""

import argparse
from pathlib import Path
from icua.extras.analysis import EventLogParser
from icua.event import MouseButtonEvent

# load configuration file
parser = argparse.ArgumentParser()
parser.add_argument(
    "-p",
    "--path",
    required=False,
    help="Path to trial directory, typically: .../<experiment.id>/<participant.id>/",
    default=Path(__file__).parent / "logs/example/",  # default example log file
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
# filter events of interest, you can use any event type here, but we are interested in mouse button events
mouse_button_events = parser.filter_events(events, MouseButtonEvent)
# convert the events from a list to a dataframe, note that `timestamp_log` is used as the column name for the logging timestamp
mouse_button_df = parser.as_dataframe(
    mouse_button_events, include=["timestamp", "button", "status"]
)
