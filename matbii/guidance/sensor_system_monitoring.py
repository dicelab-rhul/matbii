from functools import partial
from star_ray_xml import select, Select
from icua.agent import TaskAcceptabilitySensor

from ..tasks.system_monitoring import SetLightAction
from .._const import TASK_ID_SYSTEM_MONITORING, slider_id, slider_incs_id, light_id


class SystemMonitoringTaskAcceptabilitySensor(TaskAcceptabilitySensor):
    def __init__(self, *args, **kwargs):
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

    def is_active(self, task: str = None, **kwargs) -> bool:
        return True  # TODO

    def is_acceptable(self, task: str = None, **kwargs) -> bool:
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

    def is_slider_acceptable(self, _id: int):
        # sliders should be at the center position (according to SetSliderAction.acceptable_state which is incs // 2 + 1)
        state = self.beliefs[slider_id(_id)]["data-state"]
        acceptable_state = self.beliefs[slider_incs_id(_id)]["incs"] // 2
        return state == acceptable_state

    def is_light_acceptable(self, _id: int):
        return [self.is_light1_acceptable, self.is_light2_acceptable][_id - 1]()

    def is_light1_acceptable(self):
        # light 1 should be on
        return self.beliefs[light_id(1)]["data-state"] == SetLightAction.ON

    def is_light2_acceptable(self):
        # light 2 should be off
        return self.beliefs[light_id(2)]["data-state"] == SetLightAction.OFF

    def sense(self) -> list[Select]:
        lights = [f"//*[@id='{light_id(i)}']" for i in (1, 2)]
        sliders = [f"//*[@id='{slider_id(i)}']" for i in (1, 2, 3, 4)]
        slider_incs = [f"//*[@id='{slider_incs_id(i)}']" for i in (1, 2, 3, 4)]

        lights = [select(xpath=xpath, attrs=["id", "data-state"]) for xpath in lights]
        sliders = [select(xpath=xpath, attrs=["id", "data-state"]) for xpath in sliders]
        slider_incs = [
            select(xpath=xpath, attrs=["id", "incs"]) for xpath in slider_incs
        ]
        return [*lights, *sliders, *slider_incs]
