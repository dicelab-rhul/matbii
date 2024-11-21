"""Functions for extracting task events from an event log file."""

import warnings
import pandas as pd
import numpy as np
from functools import partial
from star_ray.agent.component.component import Component
from star_ray_xml import XMLState, Insert, Update, Replace, Delete
from star_ray_pygame import SVGAmbient
from icua.event import (
    Event,
    RenderEvent,
    MouseButtonEvent,
    KeyEvent,
    Select,
    UserInputEvent,
)
from icua.extras.analysis import EventLogParser

# these sensors are going to be used to get the relevant state information via their sense actions
from ...guidance import (
    SystemMonitoringTaskAcceptabilitySensor,
    TrackingTaskAcceptabilitySensor,
    # ResourceManagementTaskAcceptabilitySensor, # the sense actions are defined here...
)

# used to create resource management sense actions
from ...utils._const import (
    tank_ids,
    pump_ids,
)

# system monitoring events
from ...tasks import (
    SetSliderAction,
    SetLightAction,
    ToggleLightAction,
    TargetMoveAction,
    SetPumpAction,
    BurnFuelAction,
    PumpFuelAction,
    TogglePumpAction,
    TogglePumpFailureAction,
)


# def get_resource_management_task_events(
#     parser: EventLogParser,
#     events: list[tuple[float, Event]],
#     norm: float | int = np.inf,
# ) -> pd.DataFrame:
#     """Extracts useful data for the resource management task from the event log.

#     Columns:
#         - timestamp: float - the (logging) timestamp of the event
#         - frame: int - the frame number of the event, events with a frame number of 0 happen BEFORE the first frame is rendered to the user.
#         - user: bool - whether the event was triggered by the user or not.
#         - tank-a: float - tank a level
#         - tank-b: float - tank b level
#         - tank-c: float - tank c level
#         - tank-d: float - tank d level
#         - tank-e: float - tank e level
#         - tank-f: float - tank f level

#     Args:
#         parser (EventLogParser): parser used to parse the event log file.
#         events (list[tuple[float, Event]]): list of events that were parsed from the event log file.
#         norm (float | int, optional): the norm to use for the distance metric, either "inf" for the max norm or an integer for the p-norm.

#     Returns:
#         pd.DataFrame: dataframe with columns: ["timestamp", "frame", "user", *"tanks-{i}", *"pumps-{ij}"]
#     """
#     from matbii.utils import LOGGER

#     LOGGER.warning(
#         "`get_resource_management_task_events` is not implemented yet, the result will be an empty dataframe."
#     )
#     df = None
#     if df is None:
#         columns = [
#             "timestamp",
#             "frame",
#             "user",
#             "x",
#             "y",
#             "distance",
#         ]
#         return pd.DataFrame(columns=columns)
#     return df


def get_resource_management_task_events(
    parser: EventLogParser,
    events: list[tuple[float, Event]],
    norm: float | int = np.inf,
) -> pd.DataFrame:
    """Extracts useful data for the resource management task from the event log.

    Columns:
        - timestamp: float - the (logging) timestamp of the event
        - frame: int - the frame number of the event, events with a frame number of 0 happen BEFORE the first frame is rendered to the user.
        - user: bool - whether the event was triggered by the user or not.
        - tank-a: float - tank a level
        - tank-b: float - tank b level
        - tank-c: float - tank c level
        - tank-d: float - tank d level
        - tank-e: float - tank e level
        - tank-f: float - tank f level

    Args:
        parser (EventLogParser): parser used to parse the event log file.
        events (list[tuple[float, Event]]): list of events that were parsed from the event log file.
        norm (float | int, optional): the norm to use for the distance metric, either "inf" for the max norm or an integer for the p-norm.

    Returns:
        pd.DataFrame: dataframe with columns: ["timestamp", "frame", "user", *"tanks-{i}", *"pumps-{ij}"]
    """
    fevents = parser.filter_events(
        events,
        (
            Insert,
            Delete,
            Update,
            Replace,
            SetPumpAction,
            BurnFuelAction,
            PumpFuelAction,
            TogglePumpAction,
            TogglePumpFailureAction,
            KeyEvent,
            MouseButtonEvent,
            RenderEvent,
        ),
    )

    # # sort the events by their log timestamp
    fevents = parser.sort_by_timestamp(fevents)

    def _sense(state: XMLState):
        # sense_actions = ResourceManagementTaskAcceptabilitySensor().sense()
        # sense actions for tank states
        sense_actions = [
            Select(xpath=f"//*[@id='{id}']", attrs=["id", "data-level"])
            for id in tank_ids()
        ]
        result = sense(state, sense_actions)
        if result is None:
            result = dict()
        result_tanks = {k: v["data-level"] for k, v in result.items()}

        # actions for pump states
        sense_actions = [
            Select(xpath=f"//*[@id='{id}-button']", attrs=["id", "data-state"])
            for id in pump_ids()
        ]
        result = sense(state, sense_actions)
        # print(result)
        if result is None:
            result = dict()
        result_pumps = {k.rsplit("-", 1)[0]: v["data-state"] for k, v in result.items()}
        if len(result_pumps) == 0:
            return None
        return {**result_tanks, **result_pumps}

    df = _get_task_dataframe(fevents, _sense)
    if df is None:
        columns = [
            "timestamp",
            "frame",
            "user",
            *tank_ids(),
            *pump_ids(),
        ]
        return pd.DataFrame(columns=columns)

    # TODO combine rows if the timestamp matches
    return df


def get_tracking_task_events(
    parser: EventLogParser,
    events: list[tuple[float, Event]],
    norm: float | int = np.inf,
) -> pd.DataFrame:
    """Extracts useful data for the tracking task from the event log.

    Columns:
        - timestamp: float - the (logging) timestamp of the event
        - frame: int - the frame number of the event, events with a frame number of 0 happen BEFORE the first frame is rendered to the user.
        - user: bool - whether the event was triggered by the user or not.
        - x: float - the x coordinate of the tracking target
        - y: float - the y coordinate of the tracking target
        - distance: float - the distance to the center of the task (according to the given `norm`).

    Args:
        parser (EventLogParser): parser used to parse the event log file.
        events (list[tuple[float, Event]]): list of events that were parsed from the event log file.
        norm (float | int, optional): the norm to use for the distance metric, either "inf" for the max norm or an integer for the p-norm.

    Returns:
        pd.DataFrame: dataframe with columns: ["timestamp", "frame", "user", "x", "y", "distance"]
    """
    fn_norm = partial(np.linalg.norm, ord=norm)
    # collect all the relevant events for this task
    fevents = parser.filter_events(
        events,
        (
            Insert,
            Delete,
            Update,
            Replace,
            TargetMoveAction,
            KeyEvent,
            MouseButtonEvent,
            RenderEvent,
        ),
    )

    # # sort the events by their log timestamp
    fevents = parser.sort_by_timestamp(fevents)

    def _sense(state: XMLState):
        sense_actions = TrackingTaskAcceptabilitySensor().sense()
        result = sense(state, sense_actions)
        if result is None:
            return None
        # TODO compute distance to the center of the task
        bw, bh = (
            result[TrackingTaskAcceptabilitySensor._BOX_ID]["width"],
            result[TrackingTaskAcceptabilitySensor._BOX_ID]["height"],
        )
        bx, by = (
            result[TrackingTaskAcceptabilitySensor._BOX_ID]["x"] + bw / 2,
            result[TrackingTaskAcceptabilitySensor._BOX_ID]["y"] + bh / 2,
        )
        tw, th = (
            result[TrackingTaskAcceptabilitySensor._TARGET_ID]["width"],
            result[TrackingTaskAcceptabilitySensor._TARGET_ID]["height"],
        )
        tx, ty = (
            result[TrackingTaskAcceptabilitySensor._TARGET_ID]["x"] + tw / 2,
            result[TrackingTaskAcceptabilitySensor._TARGET_ID]["y"] + th / 2,
        )
        return dict(
            x=tx,
            y=ty,
            distance=fn_norm((tx - bx, ty - by)),
        )

    df = _get_task_dataframe(fevents, _sense)
    if df is None:
        columns = [
            "timestamp",
            "frame",
            "user",
            "x",
            "y",
            "distance",
        ]
        return pd.DataFrame(columns=columns)
    return df


def get_system_monitoring_task_events(
    parser: EventLogParser,
    events: list[tuple[float, Event]],
) -> pd.DataFrame:
    """Extracts useful data for the system monitoring task from the event log.

    Columns:
        - timestamp: float - the (logging) timestamp of the event
        - frame: int - the frame number of the event, events with a frame number of 0 happen BEFORE the first frame is rendered to the user.
        - user: bool - whether the event was triggered by the user (True) or not (False).
        - light-1: int - the state of light-1
        - light-2: int - the state of light-2
        - slider-1: int - the state of slider-1
        - slider-2: int - the state of slider-2
        - slider-3: int - the state of slider-3
        - slider-4: int - the state of slider-4

    NOTE: the number of sliders/lights is assumed to be 4/2 respectively, any alternative settings will not work here - this may be fixed in future versions.

    Args:
        parser (EventLogParser): parser used to parse the event log file.
        events (list[tuple[float, Event]]): list of events that were parsed from the event log file.

    Returns:
        pd.DataFrame: dataframe with columns: ["timestamp", "frame", "user", "light-1", "light-2", "slider-1", "slider-2", "slider-3", "slider-4"]
    """
    # these are raw events that may be triggered internally by matbii
    # insert events insert the tasks into the xml state at the start of the simulation
    fevents = parser.filter_events(
        events,
        (
            Insert,
            Delete,
            Replace,
            Update,
            SetLightAction,
            ToggleLightAction,
            SetSliderAction,
            KeyEvent,
            MouseButtonEvent,
            RenderEvent,
        ),
    )
    # sort the events by their timestamp
    fevents = parser.sort_by_timestamp(fevents)

    def _rename_column(k: str):
        return "-".join(k.split("-")[:2])

    def _sense(state: XMLState):
        # sense actions to get relevant data from the state
        sense_actions = SystemMonitoringTaskAcceptabilitySensor().sense()
        result = sense(state, sense_actions)
        if result is None:
            return None
        return {
            _rename_column(k): v["data-state"]
            for k, v in result.items()
            if "data-state" in v
        }

    df = _get_task_dataframe(fevents, _sense)
    if df is None:
        columns = [
            "timestamp",
            "frame",
            "user",
            "light-1",
            "light-2",
            "slider-1",
            "slider-2",
            "slider-3",
            "slider-4",
        ]
        return pd.DataFrame(columns=columns)
    return df


def _get_task_dataframe(
    fevents, fn_sense, user_input_event_type: type = UserInputEvent
):
    """Used internally to build a dataframe for a task."""
    # use the default state, the actual size etc. of the svg is not important for our purposes.
    # we only want to track the task events (which do not depend on the svg or window config.)
    xml_state = SVGAmbient([]).get_state()
    # sort the events by their log timestamp
    fevents = EventLogParser.sort_by_timestamp(fevents)

    def _get_task_events(fevents: list[tuple[float, Event]], avatar_ids: set[int]):
        """Execute the events in order and yield the current task state."""
        frame = 0
        for i, (t, event) in enumerate(fevents):
            if isinstance(event, RenderEvent):
                frame += 1
                continue
            if isinstance(event, user_input_event_type):
                _, avatar_id = Component.unpack_source(event)
                avatar_ids.add(avatar_id)
                continue
            event.__execute__(xml_state)  # apply the event to the state
            result = fn_sense(xml_state)
            if result is None:
                # ignore this if the the task is not yet set up, its only a probably if you see it spammed lots!
                warnings.warn(
                    f"Error sensing data for event {i} of type {type(event)}."
                )
                continue
            if event.source is None:
                warnings.warn(
                    f"Event {i} of type {type(event)} has no source, your log file is out of date."
                )
                result["agent"] = 0
            else:
                _, result["agent"] = Component.unpack_source(event)
            result["timestamp"] = t
            result["frame"] = frame
            yield result

    avatar_ids = set()

    df = pd.DataFrame(_get_task_events(fevents, avatar_ids))
    if len(avatar_ids) > 1:
        raise ValueError(
            "Multiple avatar ids inferred, this should not happen, has there been a change to the event logging system?"
        )
    if len(df) == 0:
        return None

    df["user"] = df["agent"] == next(iter(avatar_ids), float("nan"))
    df.drop(columns=["agent"], inplace=True)
    # organise columns
    start_columns = ["timestamp", "frame", "user"]
    state_columns = sorted(list(set(df.columns) - set(start_columns)))
    return df[start_columns + state_columns]


def sense(state: XMLState, sense_actions: list[Select]):
    """Sense data from the state using the provided sense actions."""

    def _sense(state: XMLState, sense_actions: list[Select]):
        for action in sense_actions:
            yield action.__execute__(state)

    data = dict()
    try:
        for obs in _sense(state, sense_actions):
            for value in obs:
                id = value.pop("id")
                data[id] = value
    except Exception:
        return None
    return data
