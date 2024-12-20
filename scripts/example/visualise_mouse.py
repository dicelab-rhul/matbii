"""Example script that will parse a raw matbii log file and extract events of a specific type."""

import argparse
import json
from pathlib import Path
from icua.extras.analysis import (
    EventLogParser,
    get_mouse_motion_events,
    get_svg_as_image,
)
import matplotlib.pyplot as plt

# load configuration file
parser = argparse.ArgumentParser()
DEFAULT_PATH = Path(__file__).parent / "example_logs/example-mouse/"

parser.add_argument(
    "-p",
    "--path",
    required=False,
    help="Path to trial directory, typically: .../<experiment.id>/<participant.id>/",
    default=DEFAULT_PATH,  # default example log file
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

mouse_motion_df = get_mouse_motion_events(parser, events)

# load the configuration file and get the size of the svg canvas
with open(Path(args.path) / "configuration.json") as f:
    config = json.load(f)
svg_size = tuple(config["ui"]["size"])

# get ready for plotting
fig, ax = plt.subplots(figsize=(4, 4))
ax.set_xlim(0, svg_size[0])
ax.set_ylim(svg_size[1], 0)

# load the initial render of the svg
image = get_svg_as_image(svg_size, events)
# show the tasks as part of the plot. NOTE: the image is already the correct size (in svg space)
ax.imshow(image)

# plot the mouse coordinate, they will be overlayed over the tasks
ax.scatter(
    mouse_motion_df["x"], mouse_motion_df["y"], marker=".", alpha=0.5, color="red"
)
plt.show()
