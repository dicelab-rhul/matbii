"""Module contains a guidance sensor for tracking the "resource management" task acceptability, see `ResourceManagementTaskAcceptabilitySensor` documentation for details."""

from typing import Any
from functools import partial
from star_ray_xml import select, Select
from .sensor_guidance import TaskAcceptabilitySensor
from ..utils._const import TASK_ID_RESOURCE_MANAGEMENT, tank_id, tank_level_id


class ResourceManagementTaskAcceptabilitySensor(TaskAcceptabilitySensor):
    """Guidance sensor for the resource management task.

    This sensor tracks a number of sub-tasks:

    - "system_monitoring.tank-a"
    - "system_monitoring.tank-b"

    The acceptability of these sub-tasks can be checked by calling the method: `ResourceManagementTaskAcceptabilitySensor.is_tank_acceptable`.

    Otherwise follow the `TaskAcceptabilitySensor` API.
    """

    def __init__(self, *args: list[Any], **kwargs: dict[str, Any]):
        """Constructor.

        Args:
            args (list[Any], optional): additional optional arguments.
            kwargs (dict[Any], optional): additional optional keyword arguments.
        """
        super().__init__(TASK_ID_RESOURCE_MANAGEMENT, *args, **kwargs)
        self._is_subtask_acceptable_map = {
            f"{self.task_name}.tank-a": partial(self.is_tank_acceptable, "a"),
            f"{self.task_name}.tank-b": partial(self.is_tank_acceptable, "b"),
        }

    def is_acceptable(self, task: str = None, **kwargs: dict[str, Any]) -> bool:  # noqa
        if task is None or task == self.task_name:
            return all([x() for x in self._is_subtask_acceptable_map.values()])
        else:
            is_acceptable = self._is_subtask_acceptable_map.get(task, None)
            if is_acceptable is None:
                raise KeyError(
                    f"Invalid subtask: {task}, doesn't exist for task {self.task_name}"
                )
            else:
                return is_acceptable()

    def is_tank_acceptable(self, _id: str) -> bool:
        """Whether the given tank is in an acceptable state.

        Acceptable: the fuel level lies in the required range.
        Unacceptable: otherwise.

        Args:
            _id (int): the id of the tank ("a" or "b")

        Returns:
            bool: True if the tank is in an acceptable state, False otherwise.
        """
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

    def sense(self, tank_ids: tuple[str, ...] = ("a", "b")) -> list[Select]:
        """Generates the sense actions that are required for checking whether the resource management task is in an acceptable state.

        The actions will request the following data:
        - the current fuel level and capacity of each main tank ("a" and "b")
        - the acceptable range of fuel for each main tank ("a" and "b")

        Args:
            tank_ids (tuple[str, str], optional): the ids of the tanks to check, defaults to ("a", "b").

        Returns:
            list[Select]: list of sense actions to take.
        """
        # interested in the fuel levels of the main tanks in the Resource Management Task
        tanks = [tank_id(i) for i in tank_ids]
        tank_levels = [tank_level_id(i) for i in tank_ids]
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
