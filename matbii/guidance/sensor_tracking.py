from star_ray_xml import select, Select
from icua.agent import TaskAcceptabilitySensor

from .._const import TASK_ID_TRACKING, tracking_box_id, tracking_target_id


class TrackingTaskAcceptabilitySensor(TaskAcceptabilitySensor):
    def __init__(self, *args, **kwargs):
        super().__init__(TASK_ID_TRACKING, *args, **kwargs)

    def is_active(self, task: str = None, **kwargs) -> bool:
        return True  # TODO

    def is_acceptable(self, task: str = None, **kwargs) -> bool:
        if task is None or task == TASK_ID_TRACKING:
            return self.is_tracking_acceptable()
        else:
            raise KeyError(
                f"Invalid subtask: {task}, doesn't exist for task {self.task_name}"
            )

    def is_tracking_acceptable(self):
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
    def is_point_in_rectangle(point, rect_min, rect_max):
        px, py = point
        min_x, min_y = rect_min
        max_x, max_y = rect_max
        return min_x <= px <= max_x and min_y <= py <= max_y

    def sense(self) -> list[Select]:
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
