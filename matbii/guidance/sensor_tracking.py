"""Module contains a guidance sensor for tracking the "tracking" task acceptability, see `TrackingTaskAcceptabilitySensor` documentation for details."""

from typing import Any
from star_ray_xml import select, Select
from icua.agent import TaskAcceptabilitySensor

from ..utils._const import TASK_ID_TRACKING, tracking_box_id, tracking_target_id


class TrackingTaskAcceptabilitySensor(TaskAcceptabilitySensor):
    """Guidance sensor for the tracking task."""

    def __init__(self, *args: list[Any], **kwargs: dict[str, Any]):
        """Constructor.

        Args:
            args (list[Any], optional): additional optional arguments.
            kwargs (dict[Any], optional): additional optional keyword arguments.
        """
        super().__init__(TASK_ID_TRACKING, *args, **kwargs)

    def is_active(self, task: str = None, **kwargs: dict[str, Any]) -> bool:  # noqa
        return True  # TODO

    def is_acceptable(self, task: str = None, **kwargs: dict[str, Any]) -> bool:  # noqa
        if task is None or task == TASK_ID_TRACKING:
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
        target = self.beliefs.get(tracking_target_id(), None)
        box = self.beliefs.get(tracking_box_id(), None)
        if target is None or box is None:
            raise ValueError(
                f"Failed to determine acceptability of task: '{TASK_ID_TRACKING}'.\n-- Missing beliefs for elements: '{tracking_target_id()}' and/or '{tracking_box_id()}'"
            )
        target_top_left = (target["x"], target["y"])
        target_size = (target["width"], target["height"])
        box_top_left = (box["x"], box["y"])
        box_bottom_right = (
            box_top_left[0] + box["width"],
            box_top_left[1] + box["height"],
        )
        target_center = (
            target_top_left[0] + target_size[0] / 2,
            target_top_left[1] + target_size[1] / 2,
        )
        return TrackingTaskAcceptabilitySensor.is_point_in_rectangle(
            target_center, box_top_left, box_bottom_right
        )

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
