"""Module contains a guidance sensor for tracking the "system monitoring" task acceptability, see :class:`SystemMonitoringTaskAcceptabilitySensor` documentation for details."""

from typing import Any
from functools import partial
from star_ray_xml import select, Select
from icua.agent import TaskAcceptabilitySensor

from ..tasks.system_monitoring import SetLightAction
from .._const import TASK_ID_SYSTEM_MONITORING, slider_id, slider_incs_id, light_id


class SystemMonitoringTaskAcceptabilitySensor(TaskAcceptabilitySensor):
    """Guidance sensor for the system monitoring task.

    This sensor tracks a number of sub-tasks:

    - "system_monitoring.light-1"
    - "system_monitoring.light-2"
    - "system_monitoring.slider-1"
    - "system_monitoring.slider-2"
    - "system_monitoring.slider-3"
    - "system_monitoring.slider-4"

    The acceptability of these sub-tasks can be checked by calling the methods: :method:`SystemMonitoringTaskAcceptabilitySensor.is_light_acceptable`, :method:`SystemMonitoringTaskAcceptabilitySensor.is_slider_acceptable`.

    Otherwise follow the :class:`TaskAcceptabilitySensor` API.
    """

    def __init__(self, *args: list[Any], **kwargs: dict[str, Any]):
        """Constructor.

        Args:
            args (list[Any], optional): additional optional arguments.
            kwargs (dict[Any], optional): additional optional keyword arguments.
        """
        super().__init__(TASK_ID_SYSTEM_MONITORING, *args, **kwargs)
        self._is_subtask_acceptable_map = {
            f"{TASK_ID_SYSTEM_MONITORING}.light-1": partial(
                self.is_light_acceptable, 1
            ),
            f"{TASK_ID_SYSTEM_MONITORING}.light-2": partial(
                self.is_light_acceptable, 2
            ),
            f"{TASK_ID_SYSTEM_MONITORING}.slider-1": partial(
                self.is_slider_acceptable, 1
            ),
            f"{TASK_ID_SYSTEM_MONITORING}.slider-2": partial(
                self.is_slider_acceptable, 2
            ),
            f"{TASK_ID_SYSTEM_MONITORING}.slider-3": partial(
                self.is_slider_acceptable, 3
            ),
            f"{TASK_ID_SYSTEM_MONITORING}.slider-4": partial(
                self.is_slider_acceptable, 4
            ),
        }

    def is_active(self, task: str = None, **kwargs: dict[str, Any]) -> bool:  # noqa
        return True  # TODO

    def is_acceptable(self, task: str = None, **kwargs: dict[str, Any]) -> bool:  # noqa
        if task is None or task == TASK_ID_SYSTEM_MONITORING:
            return all([x() for x in self._is_subtask_acceptable_map.values()])
        else:
            is_acceptable = self._is_subtask_acceptable_map.get(task, None)
            if is_acceptable is None:
                raise KeyError(
                    f"Invalid subtask: {task}, doesn't exist for task {self.task_name}"
                )
            else:
                return is_acceptable()

    def is_slider_acceptable(self, _id: int) -> bool:
        """Whether the given slider is in an acceptable state.

        Acceptable: the slider is at the central position.
        Unacceptable: otherwise.

        Args:
            _id (int): the id of the slider (1,2,3 or 4)

        Returns:
            bool: True if the slider is in an acceptable state, False otherwise.
        """
        # sliders should be at the center position to be acceptable
        state = self.beliefs[slider_id(_id)]["data-state"]
        acceptable_state = self.beliefs[slider_incs_id(_id)]["incs"] // 2 + 1
        return state == acceptable_state

    def is_light_acceptable(self, _id: int):
        """Whether the given light is in an acceptable state.

        Acceptable: light-1 is on, light-2 is off.
        Unacceptable: otherwise.

        Args:
            _id (int): the id of the light (1 or 2)

        Returns:
            bool: True if the light is in an acceptable state, False otherwise.
        """
        return [self._is_light1_acceptable, self._is_light2_acceptable][_id - 1]()

    def _is_light1_acceptable(self):
        # light 1 should be on
        return self.beliefs[light_id(1)]["data-state"] == SetLightAction.ON

    def _is_light2_acceptable(self):
        # light 2 should be off
        return self.beliefs[light_id(2)]["data-state"] == SetLightAction.OFF

    def sense(self) -> list[Select]:
        """Generates the sense actions that are required for checking whether the system monitoring task is in an acceptable state.

        The actions will request the following data:
        - the state of each light element.
        - the state of each slider element.
        - the number of increments in each slider element.

        Returns:
            list[Select]: list of sense actions to take.
        """
        lights = [f"//*[@id='{light_id(i)}']" for i in (1, 2)]
        sliders = [f"//*[@id='{slider_id(i)}']" for i in (1, 2, 3, 4)]
        slider_incs = [f"//*[@id='{slider_incs_id(i)}']" for i in (1, 2, 3, 4)]

        lights = [select(xpath=xpath, attrs=["id", "data-state"]) for xpath in lights]
        sliders = [select(xpath=xpath, attrs=["id", "data-state"]) for xpath in sliders]
        slider_incs = [
            select(xpath=xpath, attrs=["id", "incs"]) for xpath in slider_incs
        ]
        return [*lights, *sliders, *slider_incs]
