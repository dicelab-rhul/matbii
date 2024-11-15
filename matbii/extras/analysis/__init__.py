"""Module that contains useful post analysis functions."""

from .get_task import (
    get_system_monitoring_task_events,
    get_resource_management_task_events,
    get_tracking_task_events,
)

from icua.extras.analysis import (
    EventLogParser,
    get_mouse_button_events,
    get_mouse_motion_events,
    get_keyboard_events,
    get_eyetracking_events,
    get_acceptable_intervals,
    get_unacceptable_intervals,
    get_guidance_intervals,
    get_attention_intervals,
    get_start_and_end_time,
    get_svg_as_image,
    get_frame_timestamps,
    merge_intervals,
    isin_intervals,
)

__all__ = [
    "EventLogParser",
    "get_system_monitoring_task_events",
    "get_resource_management_task_events",
    "get_tracking_task_events",
    "get_mouse_button_events",
    "get_mouse_motion_events",
    "get_keyboard_events",
    "get_eyetracking_events",
    "get_acceptable_intervals",
    "get_unacceptable_intervals",
    "get_guidance_intervals",
    "get_attention_intervals",
    "get_start_and_end_time",
    "get_frame_timestamps",
    "get_svg_as_image",
    "merge_intervals",
    "isin_intervals",
]
