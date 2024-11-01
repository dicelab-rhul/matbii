"""Functions for extracting task events from an event log file."""

import warnings
import pandas as pd
from star_ray_xml import XMLState, Insert, Update, Replace, Delete
from star_ray_pygame import SVGAmbient
from icua.event import Event, MouseButtonEvent, KeyEvent, Select
from icua.extras.analysis import EventLogParser

# these sensors are going to be used to get the relevant state information via their sense actions
from ...guidance import (
    SystemMonitoringTaskAcceptabilitySensor,
    TrackingTaskAcceptabilitySensor,
)

# system monitoring events
from ...tasks import (
    SetSliderAction,
    SetLightAction,
    ToggleLightAction,
    TargetMoveAction,
)


def get_resource_management_task_events(
    parser: EventLogParser, events: list[tuple[float, Event]]
) -> pd.DataFrame:
    """TODO."""
    raise NotImplementedError("Resource management task not implemented yet.")


def get_tracking_task_events(
    parser: EventLogParser, events: list[tuple[float, Event]]
) -> pd.DataFrame:
    """Extracts useful data for the tracking task from the event log.

    Columns:
        - timestamp: float - the (logging) timestamp of the event
        - user: bool - whether the event was triggered by the user or not.
        - x: float - the x coordinate of the tracking target
        - y: float - the y coordinate of the tracking target

    Args:
        parser (EventLogParser): parser used to parse the event log file.
        events (list[tuple[float, Event]]): list of events that were parsed from the event log file.

    Returns:
        pd.DataFrame: dataframe with columns: ["timestamp", "user", "x", "y"]
    """
    # use the default state, the actual size etc. of the svg is not important for our purposes.
    # we only want to track the task events (which do not depend on the svg or window config.)
    xml_state = SVGAmbient([]).get_state()

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
        ),
    )
    print(fevents)
    # sort the events by their log timestamp
    fevents = sorted(fevents, key=lambda x: x[0])

    # sense actions to get relevant data from the state
    sense_actions = TrackingTaskAcceptabilitySensor().sense()

    def _rename_column(k: str):
        return k  # TODO?

    def _get_task_events(fevents: list[tuple[float, Event]]):
        """Execute the events in order and yield the current task state."""
        input_preceded = False
        for i, (t, event) in enumerate(fevents):
            if isinstance(event, KeyEvent):
                input_preceded = event.status == KeyEvent.DOWN
                continue  # nothing to execute on the actual mouse event
            event.__execute__(xml_state)  # apply the event to the state
            result = sense(xml_state, sense_actions)
            if result is None:
                # ignore this if the the task is not yet set up, its only a probably if you see it spammed lots!
                warnings.warn(
                    f"Error sensing data for event {i} of type {type(event)}."
                )
                continue
            result = dict(
                x=result["tracking_target"]["x"],
                y=result["tracking_target"]["y"],
            )
            result["timestamp"] = t
            # this is to distinguish between use triggered events and internal task events
            result["source"] = int(event.source) if event.source is not None else 0
            result["input_preceded"] = input_preceded
            input_preceded = False
            yield result

    df = pd.DataFrame(_get_task_events(fevents))
    # infer the sources based on mouse clicks, user events are always immediately proceeded by mouse events
    infered_user_sources = df[df["input_preceded"]]["source"].unique()
    assert (
        len(infered_user_sources) == 1
    ), "Multiple user sources inferred, this should not happen, has there been a change to the event logging system?"
    df["user"] = df["source"] == infered_user_sources[0]
    # drop unused columns
    df.drop(columns=["input_preceded", "source"], inplace=True)
    state_columns = sorted(list(set(df.columns) - set(["timestamp", "user"])))
    df = df[["timestamp", "user", *state_columns]]
    return df


def get_system_monitoring_task_events(
    parser: EventLogParser,
    events: list[tuple[float, Event]],
) -> pd.DataFrame:
    """Extracts useful data for the system monitoring task from the event log.

    Columns:
        - timestamp: float - the (logging) timestamp of the event
        - user: bool - whether the event was triggered by the user or not.
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
        pd.DataFrame: dataframe with columns: ["timestamp", "user", "light-1", "light-2", "slider-1", "slider-2", "slider-3", "slider-4"]
    """
    # use the default state, the actual size etc. of the svg is not important for our purposes.
    # we only want to track the task events (which do not depend on the svg or window config.)
    xml_state = SVGAmbient([]).get_state()

    # collect all the relevant events for this task
    fevents = []
    # these are raw events that may be triggered internally by matbii
    # insert events insert the tasks into the xml state at the start of the simulation
    fevents.extend(parser.filter_events(events, Insert))
    fevents.extend(parser.filter_events(events, Delete))
    fevents.extend(parser.filter_events(events, Update))
    fevents.extend(parser.filter_events(events, Replace))
    fevents.extend(parser.filter_events(events, SetLightAction))
    fevents.extend(parser.filter_events(events, ToggleLightAction))
    fevents.extend(parser.filter_events(events, SetSliderAction))
    fevents.extend(parser.filter_events(events, MouseButtonEvent))
    # sort the events by their log timestamp
    fevents = sorted(fevents, key=lambda x: x[0])

    # sense actions to get relevant data from the state
    sense_actions = SystemMonitoringTaskAcceptabilitySensor().sense()

    def _rename_column(k: str):
        return "-".join(k.split("-")[:2])

    def _get_task_events(fevents: list[tuple[float, Event]]):
        """Execute the events in order and yield the current task state."""
        input_preceded = False
        for i, (t, event) in enumerate(fevents):
            if isinstance(event, MouseButtonEvent):
                input_preceded = event.status == MouseButtonEvent.DOWN
                continue  # nothing to execute on the actual mouse event
            event.__execute__(xml_state)  # apply the event to the state
            result = sense(xml_state, sense_actions)
            if result is None:
                # ignore this if the the task is not yet set up, its only a probably if you see it spammed lots!
                warnings.warn(
                    f"Error sensing data for event {i} of type {type(event)}."
                )
                continue
            # get relevant data from the result
            result = {
                _rename_column(k): v["data-state"]
                for k, v in result.items()
                if "data-state" in v
            }
            result["timestamp"] = t
            # this is to distinguish between use triggered events and internal task events
            result["source"] = int(event.source) if event.source is not None else 0
            result["input_preceded"] = input_preceded
            input_preceded = False
            yield result

    df = pd.DataFrame(_get_task_events(fevents))
    # infer the sources based on mouse clicks, user events are always immediately proceeded by mouse events
    infered_user_sources = df[df["input_preceded"]]["source"].unique()
    assert (
        len(infered_user_sources) == 1
    ), "Multiple user sources inferred, this should not happen, has there been a change to the event logging system?"
    df["user"] = df["source"] == infered_user_sources[0]
    # drop unused columns
    df.drop(columns=["input_preceded", "source"], inplace=True)
    state_columns = sorted(list(set(df.columns) - set(["timestamp", "user"])))
    df = df[["timestamp", "user", *state_columns]]
    return df


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
    except Exception as e:
        print(e)
        return None
    return data
