"""Get stats from log file."""

import argparse
from pathlib import Path
from matbii.config import Configuration

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
args.dir = "C:/Users/brjw/Documents/repos/dicelab/matbii/example/logs"
args.experiment = "experiment-C"
args.participant = "P00"

# path that contains the log files
path = Path(args.dir).expanduser().resolve()
print(path)
if args.participant and args.experiment:
    # the the experiment path has been specified explicitly
    path = path / args.experiment / args.participant

files = {f.name: f for f in path.iterdir()}
# this context prevents config errors where paths cannot be resolved (since cwd has changed)
config_context = dict("experiment", dict("path", "./"))
config = Configuration.from_file(files["configuration.json"], context=config_context)
event_log = files[next(filter(lambda f: f.startswith("event_log"), files.keys()))]
print(event_log)
