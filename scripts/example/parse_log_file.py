"""Example script that will parse a raw matbii log file and extract events of a specific type."""

import argparse
from pathlib import Path
from icua.extras.analysis import EventLogParser
from icua.event import MouseButtonEvent, RenderEvent

# load configuration file
parser = argparse.ArgumentParser()
parser.add_argument(
    "-p",
    "--path",
    required=False,
    help="Path to trial directory, typically: .../<experiment.id>/<participant.id>/",
    default=Path(__file__).parent / "example_logs/example/",  # default example log file
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
# include `timestamp_log` if you want to use it (for user input events, use `timestamp` - this is actual event timestamp)
mouse_button_df = parser.as_dataframe(
    mouse_button_events, include=["timestamp", "button", "status"]
)

# You might want to include the frame number, this can be done by including "RenderEvent" in the event filter. The frame number is stored in the "frame" column.
# The frame number tells you which frame (as displayed to the user) the event occured in. You can be sure that if the event occurs in a given frame, it will be visible to the user in the NEXT frame.
mouse_button_df = parser.as_dataframe(
    parser.filter_events(events, MouseButtonEvent | RenderEvent),
    include=["timestamp", "button", "status"],
    include_frame=True,
)
print(mouse_button_df)
