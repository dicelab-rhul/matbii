"""This module contains various scripts (functions) that can be used with the argument --script. Typically they will produce some output file (e.g. a csv or plot) for some data of interest from a log file. The avaliable functions are intended to be called from the command line and not to to be used directly. The make use of the `matbii.extras.analysis` module to produce files and plots."""

import argparse
import numpy as np
import pandas as pd
from typing import Any, Literal
import matplotlib.pyplot as plt
from pathlib import Path
from ..utils import LOGGER
from ..config import Configuration


TRACKING_COLOR = "#4363d8"
RESOURCE_MANAGEMENT_COLOR = "#3cb44b"
SYSTEM_MONITORING_COLOR = "#e6194B"


def summary(**kwargs: dict[str, Any]) -> None:
    """Produce a summary from the given logging directory."""
    parser = argparse.ArgumentParser(
        description="Produce a summary from the given logging directory."
    )
    parser.add_argument(
        "--path", type=str, required=True, help="The path to the logging directory."
    )
    parser.add_argument(
        "--output",
        type=str,
        required=False,
        help="The path to the output directory, if left unspecified files will be written to <--path>/summary.",
    )
    args, _ = parser.parse_known_intermixed_args()  # ignore unknown args
    path = Path(args.path)
    log_file, config_file = _validate_logging_path(path)
    config = _load_config(config_file, context=kwargs)

    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = path / "summary"
    output_dir.mkdir(parents=True, exist_ok=True)
    _summary(log_file, config, output_dir)


# ============================================= #
# ================ INTERNAL =================== #
# ============================================= #


def _load_config(path: Path, context: dict[str, Any] | None = None) -> Configuration:
    return Configuration.from_file(path, context=context)


def _validate_logging_path(path: str | Path) -> Path:
    # check files exist
    path = Path(path)
    if not path.is_dir():
        raise FileNotFoundError(
            f"Logging directory does not exist or is not a directory: {path.as_posix()}"
        )
    # get configuration file
    config_files = list(path.glob("*.json"))
    if len(config_files) == 0:
        raise FileNotFoundError(
            f"No configuration file found in logging directory: {path.as_posix()}"
        )
    if len(config_files) > 1:
        raise ValueError(
            f"Multiple configuration files found in logging directory: {path.as_posix()}"
        )

    # get "*.log" files from directory
    log_files = list(path.glob("*.log"))
    if len(log_files) == 0:
        raise FileNotFoundError(
            f"No log files found in logging directory: {path.as_posix()}"
        )
    if len(log_files) > 1:
        raise ValueError(
            f"Multiple logs files found in logging directory: {path.as_posix()}"
        )

    return log_files[0], config_files[0]


def _summary(
    log_file: Path,
    config: Configuration,
    output_dir: Path | None = None,
    **kwargs: dict[str, Any],
):
    from .analysis import (
        EventLogParser,
        get_mouse_button_events,
        get_mouse_motion_events,
        get_keyboard_events,
        get_system_monitoring_task_events,
        get_tracking_task_events,
        get_resource_management_task_events,
        get_eyetracking_events,
        get_acceptable_intervals,
        get_unacceptable_intervals,
        get_attention_intervals,
        get_guidance_intervals,
        get_start_and_end_time,
        get_frame_timestamps,
        get_svg_as_image,
    )

    parser = EventLogParser()
    parser.discover_event_classes("matbii")
    events = list(
        parser.parse(log_file, relative_start=kwargs.get("relative_start", True))
    )
    LOGGER.debug(f"Writing output to {output_dir.as_posix()}")
    get_mouse_button_events(parser, events).to_csv(
        output_dir / "mouse_button.csv", index=False
    )
    mouse_motion_df = get_mouse_motion_events(parser, events)
    mouse_motion_df.to_csv(output_dir / "mouse_motion.csv", index=False)
    keyboard_df = get_keyboard_events(parser, events)
    keyboard_df.to_csv(output_dir / "keyboard.csv", index=False)
    eyetracking_df = get_eyetracking_events(parser, events)
    eyetracking_df.to_csv(output_dir / "eyetracking.csv", index=False)
    get_system_monitoring_task_events(parser, events).to_csv(
        output_dir / "system_monitoring.csv", index=False
    )
    get_tracking_task_events(parser, events).to_csv(
        output_dir / "tracking.csv", index=False
    )

    get_resource_management_task_events(parser, events).to_csv(
        output_dir / "resource_management.csv"
    )
    frame_timestamps = pd.DataFrame(get_frame_timestamps(events), columns=["timestamp"])
    frame_timestamps.to_csv(output_dir / "frame_timestamps.csv", index=False)

    # get intervals
    _intervals_as_df(dict(get_acceptable_intervals(events))).to_csv(
        output_dir / "acceptable_intervals.csv", index=False
    )
    _intervals_as_df(dict(get_unacceptable_intervals(events))).to_csv(
        output_dir / "unacceptable_intervals.csv", index=False
    )
    _intervals_as_df(dict(get_guidance_intervals(events))).to_csv(
        output_dir / "guidance_intervals.csv", index=False
    )

    # get attention intervals - mouse, gaze, fixation
    _intervals_as_df(dict(get_attention_intervals(mouse_motion_df))).to_csv(
        output_dir / "attention_intervals_mouse.csv", index=False
    )

    # TODO: get attention intervals - input (mouse + keyboard)

    _intervals_as_df(dict(get_attention_intervals(eyetracking_df))).to_csv(
        output_dir / "attention_intervals_gaze.csv", index=False
    )

    # fixation intervals
    fixation_df = eyetracking_df[eyetracking_df["fixated"]]
    # deal with empty eyetracking df
    if fixation_df.empty:
        columns = list(eyetracking_df.columns)
        columns.remove("fixated")
        fixation_df = pd.DataFrame(columns=columns)
    _intervals_as_df(dict(get_attention_intervals(fixation_df))).to_csv(
        output_dir / "attention_intervals_fixation.csv", index=False
    )

    # record start and end times
    start_time, end_time = get_start_and_end_time(events)

    # make plots
    # output_dir = output_dir / "plots"
    # output_dir.mkdir(parents=True, exist_ok=True)
    attention_mode = config.guidance.attention_mode
    fig = _summary_plot(output_dir, attention_mode=attention_mode)
    fig.savefig(output_dir / "summary.png", bbox_inches="tight")

    # plot eyetracking if we have any

    if not mouse_motion_df.empty:
        img = get_svg_as_image((config.ui.width, config.ui.height), events)
        fig, ax = plt.subplots(figsize=(4, 4))
        fig.suptitle("Mouse motion")
        ax.imshow(img)
        plt.scatter(
            mouse_motion_df["x"],
            mouse_motion_df["y"],
            marker=".",
            alpha=0.5,
            color="red",
        )
        fig.savefig(output_dir / "mouse_motion.png", bbox_inches="tight")

    if not eyetracking_df.empty:
        img = get_svg_as_image((config.ui.width, config.ui.height), events)
        fig, ax = plt.subplots(figsize=(4, 4))
        fig.suptitle("Eyetracking")
        ax.imshow(img)
        plt.scatter(
            eyetracking_df["x"][~eyetracking_df["fixated"]],
            eyetracking_df["y"][~eyetracking_df["fixated"]],
            marker=".",
            alpha=0.2,
            color="blue",
        )
        plt.scatter(
            eyetracking_df["x"][eyetracking_df["fixated"]],
            eyetracking_df["y"][eyetracking_df["fixated"]],
            marker=".",
            alpha=0.8,
            color="red",
        )
        fig.savefig(output_dir / "eyetracking.png", bbox_inches="tight")

    plt.show()


def _summary_plot(
    path: Path,
    attention_mode: Literal["mouse", "fixation", "gaze"] = "mouse",
    guidance_colour: str = "red",
    attention_colour: str = "green",
    system_monitoring_colour: str = SYSTEM_MONITORING_COLOR,
    tracking_colour: str = TRACKING_COLOR,
    resource_management_colour: str = RESOURCE_MANAGEMENT_COLOR,
):
    import matplotlib.pyplot as plt
    from icua.extras.analysis import plot_intervals, plot_timestamps

    fig, ax = plt.subplots(figsize=(20, 2))
    task_data = dict(
        system_monitoring=dict(ylim=(0, 1 / 3), colour=system_monitoring_colour),
        tracking=dict(ylim=(1 / 3, 2 / 3), colour=tracking_colour),
        resource_management=dict(ylim=(2 / 3, 1), colour=resource_management_colour),
    )
    acceptable_intervals = pd.read_csv(path / "acceptable_intervals.csv")
    unacceptable_intervals = pd.read_csv(path / "unacceptable_intervals.csv")
    guidance_intervals = pd.read_csv(path / "guidance_intervals.csv")
    try:
        attention_intervals = pd.read_csv(
            path / f"attention_intervals_{attention_mode}.csv"
        )
    except FileNotFoundError:
        avaliable = [
            p.name.split(".")[0].split("_")[-1]
            for p in path.glob(path / "attention_intervals_*.csv")
        ]
        raise ValueError(
            f"Attention intervals for mode {attention_mode} not found, available: {avaliable}."
        )
    first = True
    for task, data in task_data.items():
        plot_intervals(
            acceptable_intervals[acceptable_intervals["task"] == task],
            color=tracking_colour,
            alpha=0.5,
            label="acceptable" if first else None,
            ymin=data["ylim"][0],
            ymax=data["ylim"][1],
            ax=ax,
        )
        plot_intervals(
            unacceptable_intervals[unacceptable_intervals["task"] == task],
            color="black",
            alpha=0.1,
            label="unacceptable" if first else None,
            ymin=data["ylim"][0],
            ymax=data["ylim"][1],
            ax=ax,
        )
        plot_intervals(
            guidance_intervals[guidance_intervals["task"] == task],
            color=guidance_colour,
            alpha=0.2,
            ax=ax,
            label="guidance" if first else None,
            ymin=data["ylim"][0] + 0.05,
            ymax=data["ylim"][1] - 0.05,
        )
        plot_intervals(
            attention_intervals[attention_intervals["task"] == task],
            color=attention_colour,
            alpha=0.2,
            ax=ax,
            label=f"attention_{attention_mode}" if first else None,
            ymin=data["ylim"][0] + 0.05,
            ymax=data["ylim"][1] - 0.05,
        )

        df = pd.read_csv(path / f"{task}.csv")
        # plot the timestamps for the task changed its state due to the task specific agent.
        plot_timestamps(
            df["timestamp"][~df["user"]],
            color="black",
            alpha=0.5,
            label="task schedule" if first else None,
            ymin=data["ylim"][0] + 0.1,
            ymax=data["ylim"][1] - 0.1,
            ax=ax,
        )
        # plot the timestamps for the task changed its state due to the user.
        plot_timestamps(
            df["timestamp"][df["user"]],
            color="red",
            alpha=0.5,
            label="user input" if first else None,
            ymin=data["ylim"][0] + 0.1,
            ymax=data["ylim"][1] - 0.1,
            ax=ax,
        )
        first = False

    # # plot the start and end times - this is the time of the first and last rendered frame.
    # fig = plot_timestamps(
    #     np.array([start_time, end_time]),
    #     color="black",
    #     ax=ax,
    #     linestyle="--",
    #     label="start/end",
    # )
    plt.legend(loc="lower center", bbox_to_anchor=(0.5, 1), ncol=100)
    plt.tight_layout()
    return fig


def _intervals_as_df(intervals: dict[str, np.ndarray]) -> pd.DataFrame:
    def _gen():
        # yield an empty dataframe to handle the case where no intervals are found
        for task, i in intervals.items():
            if len(i) > 0:
                yield pd.DataFrame({"t1": i[:, 0], "t2": i[:, 1], "task": task})

    result = list(_gen())
    if len(result) == 0:
        return pd.DataFrame(columns=["t1", "t2", "task"])
    df = pd.concat(result)
    df.sort_values(by="t1", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df
