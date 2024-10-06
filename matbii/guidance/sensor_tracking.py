"""Module contains a guidance sensor for tracking the "tracking" task acceptability, see `TrackingTaskAcceptabilitySensor` documentation for details."""

from typing import Any
from star_ray.event.observation_event import Observation
from star_ray_xml import select, Select
from .sensor_guidance import TaskAcceptabilitySensor

from ..utils._const import TASK_ID_TRACKING, tracking_box_id, tracking_target_id


class TrackingTaskAcceptabilitySensor(TaskAcceptabilitySensor):
    """Guidance sensor for the tracking task."""

    _BOX_ID = tracking_box_id()
    _TARGET_ID = tracking_target_id()

    def __init__(self, *args: list[Any], **kwargs: dict[str, Any]):
        """Constructor.

        Args:
            args (list[Any], optional): additional optional arguments.
            kwargs (dict[Any], optional): additional optional keyword arguments.
        """
        super().__init__(TASK_ID_TRACKING, *args, **kwargs)
        # initialise beliefs about the tracking tasks
        self.beliefs[TrackingTaskAcceptabilitySensor._BOX_ID] = dict()
        self.beliefs[TrackingTaskAcceptabilitySensor._TARGET_ID] = dict()

    def is_acceptable(self, task: str = None, **kwargs: dict[str, Any]) -> bool:  # noqa
        if task is None or task == self.task_name:
            return self.is_tracking_acceptable()
        else:
            raise KeyError(
                f"Invalid subtask: {task}, doesn't exist for task {self.task_name}"
            )

    def is_tracking_acceptable(self) -> bool:
        """Determines whether the tracking task is in an acceptable state.

        Acceptable: "target" is within the central box of the task.
        Unacceptable: otherwise.

        Raises:
            ValueError: if there is missing observational data about the task - this may mean the task is not active.

        Returns:
            bool: whether the task is in an acceptable state.
        """
        try:
            target = self.beliefs.get(TrackingTaskAcceptabilitySensor._TARGET_ID, None)
        except KeyError:
            raise KeyError(
                f"Failed to determine acceptability of task: '{TASK_ID_TRACKING}'.\n-- Missing beliefs for elements: '{TrackingTaskAcceptabilitySensor._TARGET_ID}'"
            )
        try:
            box = self.beliefs.get(TrackingTaskAcceptabilitySensor._BOX_ID, None)
        except KeyError:
            raise KeyError(
                f"Failed to determine acceptability of task: '{TASK_ID_TRACKING}'.\n-- Missing beliefs for elements: '{TrackingTaskAcceptabilitySensor._BOX_ID}'"
            )
        return TrackingTaskAcceptabilitySensor.is_point_in_rectangle(
            target["xy"], box["tl"], box["br"]
        )

    def on_observation(self, observation: Observation):
        """Update beliefs about the tracking task based on the incoming observation.

        Args:
            observation (Observation): observation
        """
        for data in observation.values:
            try:
                if data["id"] == TrackingTaskAcceptabilitySensor._TARGET_ID:
                    tl = (data["x"], data["y"])
                    size = (data["width"], data["height"])
                    xy = (tl[0] + size[0] / 2, tl[1] + size[1] / 2)
                    self.beliefs[TrackingTaskAcceptabilitySensor._TARGET_ID]["xy"] = xy
                    self.beliefs[TrackingTaskAcceptabilitySensor._TARGET_ID]["size"] = (
                        size
                    )
                elif data["id"] == TrackingTaskAcceptabilitySensor._BOX_ID:
                    tl = (data["x"], data["y"])
                    self.beliefs[TrackingTaskAcceptabilitySensor._BOX_ID]["tl"] = tl
                    self.beliefs[TrackingTaskAcceptabilitySensor._BOX_ID]["br"] = (
                        tl[0] + data["width"],
                        tl[1] + data["height"],
                    )
            except KeyError:
                raise KeyError(
                    f"Observation: {observation} doesn't contain the required `id` attribute."
                )

    def sense(self) -> list[Select]:
        """Generates the sense actions that are required for checking whether the tracking task is in an acceptable state.

        The actions will request the following data:
        - the bounds of the target element.
        - the bounds of the central box of the tracking task.

        Returns:
            list[Select]: list of sense actions to take.
        """
        return [
            select(
                xpath=f"//*[@id='{tracking_target_id()}']",
                attrs=["id", "x", "y", "width", "height"],
            ),
            select(
                xpath=f"//*[@id='{tracking_box_id()}']",
                attrs=["id", "x", "y", "width", "height"],
            ),
        ]

    @staticmethod
    def is_point_in_rectangle(
        point: tuple[float, float],
        rect_min: tuple[float, float],
        rect_max: tuple[float, float],
    ) -> bool:
        """Checks wether the given `point` is within the rectangle as specified by the top left and bottom right coordinate.

        Args:
            point (tuple[float, float]): point to check.
            rect_min (tuple[float,float]): top left.
            rect_max (tuple[float,float]): bottom right.

        Returns:
            bool: whether the point is in the rectangle.
        """
        px, py = point
        min_x, min_y = rect_min
        max_x, max_y = rect_max
        return min_x <= px <= max_x and min_y <= py <= max_y
