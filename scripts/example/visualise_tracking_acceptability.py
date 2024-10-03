"""TODO."""

import argparse
from pathlib import Path
from icua.extras.analysis import (
    EventLogParser,
    get_acceptable_intervals,
    merge_intervals,
)
from icua.event import KeyEvent
from matbii.tasks.tracking import TargetMoveAction
import numpy as np
import pandas as pd
from star_ray import Event
from star_ray_xml import Insert
from lxml import etree

# load configuration file
parser = argparse.ArgumentParser()
parser.add_argument(
    "-p",
    "--path",
    required=False,
    help="Path to trial directory, typically: .../<experiment.id>/<participant.id>/",
    default=Path(__file__).parent
    / "logs/example-tracking-only/",  # default example log file
)

args = parser.parse_args()
parser = EventLogParser()
parser.discover_event_classes("matbii")
events = list(parser.parse(parser.get_event_log_file(args.path)))

# timestamp and timestamp_log are effectively the same here
dfs = parser.as_dataframes(events)


def resolve_tracking_dataframe(df: pd.DataFrame):
    """Resolve the position in the tracking dataframe."""
    df[["x", "y"]] = (
        np.array(df["direction"].to_list()) * df["speed"].to_numpy()[:, np.newaxis]
    ).cumsum(axis=0)
    return (
        df[["timestamp_log", "x", "y"]]
        .copy()
        .rename(columns={"timestamp_log": "timestamp"})
    )


def is_in_intervals(x: np.ndarray, intervals: np.ndarray) -> np.ndarray:
    """Computes a boolean array determining whether each timestamp in `x` is in an interval in `intervals`.

    Args:
        x (np.ndarray): timestamps of shape (n,)
        intervals (np.ndarray): intervals of shape (n, 2) where each interval is (start, end)

    Returns:
        np.ndarray: resulting indicator array
    """
    start_in_interval = intervals[:, 0][:, np.newaxis] <= x
    end_in_interval = intervals[:, 1][:, np.newaxis] >= x
    in_interval = start_in_interval & end_in_interval
    return np.any(in_interval, axis=0)


df_tracking = resolve_tracking_dataframe(dfs[TargetMoveAction])

# Compute the task acceptability
intervals = dict(get_acceptable_intervals(events))["tracking"]
df_tracking["is_acceptable"] = is_in_intervals(
    df_tracking["timestamp"].to_numpy(), intervals
)
# this shift is always needed because acceptability events are triggered AFTER the state has changed, the
# change that triggered the acceptability event wont be in the acceptability interval (by a single cycle),
# this is an important timing gotcha which needs some consideration for each task
df_tracking["is_acceptable"] = df_tracking["is_acceptable"].shift(
    -1, fill_value=df_tracking["is_acceptable"].iloc[-1]
)

# Compute task interaction (via keyboard events)

df_keyboard = dfs[KeyEvent][["timestamp", "status", "key"]]
keyboard_intervals = []
for group, df_key in df_keyboard.groupby(by="key"):
    assert (df_key["status"] != 2).all()
    # these can be fixed using start and end time, but from speed here we go!
    assert df_key["status"].iloc[0] == 1  # key pressed for the first time
    assert df_key["status"].iloc[-1] == 0  # key released at the end
    keyboard_intervals.append(df_key["timestamp"].to_numpy().reshape(-1, 2))

# these are the times at which ANY key was pressed (the user is presumed to be interacting with the tracking tasks)
keyboard_intervals = merge_intervals(*keyboard_intervals)
df_tracking["is_key_pressed"] = is_in_intervals(
    df_tracking["timestamp"].to_numpy(), keyboard_intervals
)


def get_task_data(parser, events: list[tuple[float, Event]]):
    """Get svg data relevant to tasks from the event log."""

    def get_tracking_data(root):
        tracking_box = root.xpath(".//*[@id='tracking_box']")[0]
        data = dict()
        data["tracking_box"] = dict(
            x=float(tracking_box.get("x")),
            y=float(tracking_box.get("y")),
            width=float(tracking_box.get("width")),
            height=float(tracking_box.get("height")),
        )
        target = root.xpath(".//*[@id='tracking_target']")[0]
        data["tracking_target"] = dict(
            cx=float(target.get("x")) + float(target.get("width")) / 2,
            cy=float(target.get("y")) + float(target.get("height")) / 2,
            width=float(target.get("width")),
            height=float(target.get("height")),
        )
        return data

    data_funs = dict(tracking=get_tracking_data)
    # TODO handle task enable/disable during simulation?

    insert_events = parser.filter_events(events, Insert)
    result = dict()
    for t, event in insert_events:
        task_root = etree.fromstring(event.element)
        # get some useful data from this...
        task_id = task_root.get("id")
        data = dict(
            task_id=task_id,
            x=float(task_root.get("x")),
            y=float(task_root.get("y")),
            width=float(task_root.get("width")),
            height=float(task_root.get("height")),
            **data_funs[task_id](task_root),
        )
        result[task_id] = data
    return result


tracking_data = get_task_data(parser, events)["tracking"]


def visualise_task_tracking():
    """Visualise the movement of the target in the tracking task."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    fig, ax = plt.subplots(figsize=(6, 6))
    fig.tight_layout()
    ax.set_xlim(tracking_data["x"], tracking_data["x"] + tracking_data["width"])
    ax.set_ylim(tracking_data["y"], tracking_data["y"] + tracking_data["height"])
    ax.invert_yaxis()  # ensure same layout as svg format (origin is top left)

    tracking_box = tracking_data["tracking_box"]
    ax.add_patch(
        Rectangle(
            (
                tracking_box["x"],
                tracking_box["y"],  # bottom left corner
            ),
            tracking_box["width"],
            tracking_box["height"],
            edgecolor="black",
            facecolor="none",
            linewidth=1,
        )
    )
    target_start_position = np.array(
        (tracking_data["tracking_target"]["cx"], tracking_data["tracking_target"]["cy"])
    )
    target_positon = target_start_position + df_tracking[["x", "y"]].to_numpy()
    # print(target_positon)
    plt.scatter(
        *target_positon.T,
        marker=".",
        c=df_tracking["is_acceptable"].to_numpy().astype(int),
    )
    # plot center of tracking task
    plt.scatter(
        [tracking_data["width"] / 2],
        [tracking_data["height"] / 2],
        color="red",
    )
    plt.show()


# visualise the target moving in the tracking task
# visualise_task_tracking()

# Compute the reaction time or "score" of the user for the tracking task, there are a few options:

# 1. the length of the failure (duration of unacceptable -> acceptable)
# 2. from unacceptable to the time they interact with the task (based on keyboard interactions)
# 3. from unacceptable to the time they gaze at the task (as a proxy for shifting attention)
# 4. the distance from the center of the task

# CASE 1. is simply the length of the acceptability intervals
# mean_failure_duration = (intervals[:, 1] - intervals[:, 0]).mean()

# CASE 2:
#
