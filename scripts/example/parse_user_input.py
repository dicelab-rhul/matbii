"""Example script to extract events from a log file in a convenient format (pandas dataframe)."""

import icua.extras.analysis as analysis

DEFAULT_PATH = "C:/Users/brjw/Documents/repos/dicelab/matbii/scripts/example/logs/test-mouse/event_log_2024-11-01-10-38-22.log"

# set up the parser
parser = analysis.EventLogParser()
parser.discover_event_classes("matbii")
events = list(parser.parse(DEFAULT_PATH, relative_start=True))

# get mouse button events
mouse_button_df = analysis.get_mouse_button_events(parser, events)
print(mouse_button_df)

# get mouse motion events
mouse_motion_df = analysis.get_mouse_motion_events(parser, events)
print(mouse_motion_df)

# get keyboard events
keyboard_df = analysis.get_keyboard_events(parser, events)
print(keyboard_df)
