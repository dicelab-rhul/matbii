"""Get stats from log file."""

import argparse
from pathlib import Path
import typing
from matbii.utils import LOGGER
from pprint import pprint
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from icua.extras.analysis import (
    EventLogParser,
    plot_timestamps,
    plot_intervals,
    get_guidance_intervals,
    get_acceptable_intervals,
)
from star_ray import Event
from star_ray_xml import Update
from icua.event import (
    MouseButtonEvent,
    WindowOpenEvent,
    WindowCloseEvent,
    WindowResizeEvent,
    WindowMoveEvent,
    MouseMotionEvent,
    ScreenSizeEvent,
    KeyEvent,
    RenderEvent,
    EyeMotionEvent,
)

# load configuration file
parser = argparse.ArgumentParser()
parser.add_argument(
    "-p",
    "--path",
    required=False,
    help="Path to trial directory, typically: .../<experiment.id>/<participant.id>/",
    default="./",
)

args = parser.parse_args()

# TODO remove this is just for testing!
args.path = (
    "C:/Users/brjw/Documents/repos/dicelab/matbii/test/test_logs/eyetracking/P00"
)
# args.path = "C:/Users/brjw/Documents/repos/dicelab/matbii/example/logs/C/P00"

path = Path(args.path).expanduser().resolve()
if not path.exists():
    raise FileNotFoundError(f"Directory {path.as_posix()} not found")

# this context prevents config errors where paths cannot be resolved (since cwd has changed)
# config_context = dict(experiment=dict(path="./"))
# config = Configuration.from_file(files["configuration.json"], context=config_context)
event_log_file = next(
    filter(
        lambda f: f.name.startswith("event_log") or f.suffix == ".log", path.iterdir()
    )
)

parser = EventLogParser()
parser.discover_event_classes("matbii")

pprint(parser._event_cls_map.keys())
events = list(parser.parse(event_log_file))


def summarise():
    """TODO. -- plots a summary task acceptability, guidance and user input."""
    TRACKING_COLOR = "#4363d8"
    RESOURCE_MANAGEMENT_COLOR = "#3cb44b"
    SYSTEM_MONITORING_COLOR = "#e6194B"

    TASK_PLOT_DATA = {
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
        color = TASK_PLOT_DATA[task]["color"]
        ymin = TASK_PLOT_DATA[task]["ymin"]
        ymax = TASK_PLOT_DATA[task]["ymax"]
        plot_intervals(intervals, color=color, alpha=0.3, ymin=ymin, ymax=ymax, ax=ax)
        ax = plt.gca()

    for task, intervals in get_guidance_intervals(events):
        ymin = TASK_PLOT_DATA[task]["ymin"] * 1.05
        ymax = TASK_PLOT_DATA[task]["ymax"] * 0.95
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


def plot_eyetracking(
    events: list[Event], space=typing.Literal["screen", "window", "canvas"]
):
    """TODO."""

    def _get_events(events: list[Event], type: type[Event]) -> list[Event]:
        return list(filter(lambda x: isinstance(x[1], type), events))

    def _get_static_property(_type: type[Event], name: str):
        pevents = _get_events(events, _type)
        if len(pevents) > 1:
            LOGGER.warning(
                f"{name.capitalize()} changed during run, cannot statically plot events."
            )
        return pevents[0][1]

    def _new_figure(size: tuple[int, int], figsize: float = 5):
        aspect_ratio = size[0] / size[1]
        fig = plt.figure(figsize=(figsize * aspect_ratio, figsize))
        ax = plt.gca()
        ax.set_xlim(0, size[0])
        ax.set_ylim(0, size[1])
        ax.invert_yaxis()
        ax.xaxis.set_ticks_position("top")
        return fig, ax

    window_size = _get_static_property(WindowResizeEvent, name="window size").size
    screen_size = _get_static_property(ScreenSizeEvent, name="screen size").size
    window_position = _get_static_property(
        WindowMoveEvent, name="window position"
    ).position

    if space == "canvas":
        # get canvas size
        updates = _get_events(events, Update)
        cattrs = updates[0][1].attrs  # TODO this might break in future versions...
        canvas_size = cattrs["width"], cattrs["height"]
        # this is not relevant here, it gives the position of the canvas on the window
        # (althought this may not be true either, it will depend on the layout in star_ray_pygame Avatar
        # canvas_position = cattrs["x"], cattrs["y"]
        fig, ax = _new_figure(canvas_size)

        # visualise only on canvas
        mouse_motion = _get_events(events, MouseMotionEvent)
        if mouse_motion:
            mouse_motion = np.array([e[1].position for e in mouse_motion])
            plt.scatter(
                *mouse_motion.T,
                marker=".",
                color="black",
                alpha=0.2,
                label="mouse motion",
            )

        eye_motion = _get_events(events, EyeMotionEvent)
        if eye_motion:
            eye_motion = np.array([e[1].position for e in eye_motion])
            plt.scatter(
                *eye_motion.T, marker=".", color="red", alpha=0.2, label="eye motion"
            )

        plt.show()

    if space == "screen":
        fig, ax = _new_figure(screen_size)
        # matbii window on screen
        rectangle = patches.Rectangle(
            window_position, *window_size, linewidth=1, edgecolor="r", facecolor="none"
        )
        ax.add_patch(rectangle)

        # mouse_motion = _get_events(events, MouseMotionEvent)
        # mouse_motion = np.array([e[1].position_raw for e in mouse_motion])
        # mouse_motion += np.array(window_position)
        # plt.scatter(*mouse_motion.T)
        # plt.show()

        eye_events = _get_events(events, EyeMotionEvent)
        screen_positions = np.array([e[1].position_screen for e in eye_events])
        screen_positions *= np.array(screen_size)[np.newaxis, :]
        print(screen_positions.shape)
        plt.scatter(*screen_positions.T)
        plt.show()


plot_eyetracking(events, space="canvas")
plt.show()
