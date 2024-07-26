from functools import partial
from star_ray_xml import select, Select
from icua.agent import TaskAcceptabilitySensor

from .._const import TASK_ID_RESOURCE_MANAGEMENT, tank_id, tank_level_id


class ResourceManagementTaskAcceptabilitySensor(TaskAcceptabilitySensor):
    def __init__(self, *args, **kwargs):
        super().__init__(TASK_ID_RESOURCE_MANAGEMENT, *args, **kwargs)
        self._is_subtask_acceptable_map = {
            f"{TASK_ID_RESOURCE_MANAGEMENT}.tank-a": partial(
                self.is_tank_acceptable, "a"
            ),
            f"{TASK_ID_RESOURCE_MANAGEMENT}.tank-b": partial(
                self.is_tank_acceptable, "b"
            ),
        }

    def is_active(self, task: str = None, **kwargs) -> bool:
        return True  # TODO

    def is_acceptable(self, task: str = None, **kwargs) -> bool:
        if task is None or task == TASK_ID_RESOURCE_MANAGEMENT:
            return all([x() for x in self._is_subtask_acceptable_map.values()])
        else:
            is_acceptable = self._is_subtask_acceptable_map.get(task, None)
            if is_acceptable is None:
                raise KeyError(
                    f"Invalid subtask: {task}, doesn't exist for task {self.task_name}"
                )
            else:
                return is_acceptable()

    def is_tank_acceptable(self, _id: str):
        tank = self.beliefs[tank_id(_id)]
        tank_level = self.beliefs[tank_level_id(_id)]

        fuel_capacity = tank["data-capacity"]
        fuel_level = tank["data-level"]
        acceptable_level = tank_level["data-level"] * fuel_capacity
        acceptable_range2 = (tank_level["data-range"] * fuel_capacity) / 2
        return (
            fuel_level >= acceptable_level - acceptable_range2
            and fuel_level <= acceptable_level + acceptable_range2
        )

    def sense(self) -> list[Select]:
        # interested in the fuel levels of the main tanks in the Resource Management Task
        tanks = [tank_id(i) for i in ("a", "b")]
        tank_levels = [tank_level_id(i) for i in ("a", "b")]
        tank_selects = [
            select(
                xpath=f"//*[@id='{id}']", attrs=["id", "data-capacity", "data-level"]
            )
            for id in tanks
        ]
        tank_level_selects = [
            select(xpath=f"//*[@id='{id}']", attrs=["id", "data-level", "data-range"])
            for id in tank_levels
        ]
        return [*tank_selects, *tank_level_selects]
