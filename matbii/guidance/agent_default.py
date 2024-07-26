import time
import random

from star_ray.agent import Actuator, Sensor, observe
from icua.event import USER_INPUT_TYPES, MouseMotionEvent, EyeMotionEvent
from icua.agent import (
    GuidanceActuator,
    ArrowGuidanceActuator, 
    BoxGuidanceActuator,
    TaskAcceptabilitySensor,
)
from icua.utils import LOGGER
from star_ray.environment import State  # type hint
from .agent_base import GuidanceAgent

__all__ = ("DefaultGuidanceAgent", "DefaultGuidanceActuator", "ArrowGuidanceActuator", 
    "BoxGuidanceActuator")


class DefaultGuidanceAgent(GuidanceAgent):
    # used to break ties when multiple tasks could be highlighted. See `break_guidance_tie` method below.
    BREAK_TIES = ("random", "longest", "since")

    def __init__(
        self,
        sensors: list[Sensor],
        actuators: list[Actuator],
        break_ties: str = "random",
        grace_period: float = 3.0,
        counter_factual: bool = False,
        **kwargs,
    ):
        super().__init__(
            sensors,
            actuators, 
            **kwargs
        )

        # this agent is tracking the following tasks (based on the provided sensors)
        self._tracking_tasks = [
            s.task_name
            for s in filter(
                lambda x: isinstance(x, TaskAcceptabilitySensor), self.sensors
            )
        ]

        # time since tasks went into an unacceptable state
        self._task_unacceptable_start: dict[str, float] = None
        # time since tasks become inactive
        self._task_inactive_start: dict[str, float] = None
        # TODO track the time since user input (gaze) has been provided, we can trigger an error if this is too long
        self._missing_gaze_since: float = None
        # guidance shown on task?
        self._guidance_on_task: str = None
        # time since guidance was shown for each task (for grace period)
        self._guidance_last: dict[str, float] = None
        # method to use to break ties when more than one task meets the guidance criteria
        self._break_ties = break_ties  # ("random", "longest", "since")
        if self._break_ties not in ("random", "longest", "since"):
            raise ValueError(
                f"Invalid argument: `break_ties` {self._break_ties} must be one of {DefaultGuidanceAgent.BREAK_TIES}"
            )
        # time to wait before showing guidance again on a task (can be zero)
        self._grace_period = grace_period  # TODO
        if self._grace_period < 0.0:
            raise ValueError(
                f"Invalid argument: `grace_period` {self._grace_period} must be > 0 "
            )
        # whether to actually display guidance, or just trigger a guidance event
        self._counter_factual = counter_factual

    def __initialise__(self, state: State):
        super().__initialise__(state)
        # initialise task unacceptability and inactivity
        start_time = time.time()  # not accurate but good enough
        self._task_inactive_start = {t: start_time for t in self._tracking_tasks}
        self._task_unacceptable_start = {t: start_time for t in self._tracking_tasks}
        # initialise time to last guidance shown
        self._guidance_last = {t: start_time for t in self._tracking_tasks}

    def show_guidance(self, task: str):
        """Show guidance for a given task.

        If overriding you must call super() to ensure consistent behaviour.

        Args:
            task (str): the task to show guidance for.
        """
        self._guidance_on_task = task
        for actuator in self.guidance_actuators:
            actuator.show_guidance(task=task)

    def hide_guidance(self, task: str):
        """Hide guidance for a given task.

        If overriding you must call super() to ensure consistent behaviour.

        Args:
            task (str): the task to hide guidance for.
        """
        # TODO trigger event here! this will be used in post analysis, ensure that counterfactual guidance is also a thing!
        self._guidance_on_task = None
        for actuator in self.guidance_actuators:
            actuator.hide_guidance(task=task)
        # update the last time guidance was shown for the given task (for the grace period check)
        self._guidance_last[task] = time.time()

    def __cycle__(self):
        super().__cycle__()
        gaze_elements, gaze = self.mouse_at_elements, self.mouse_position
        gaze_elements, gaze = self.gaze_at_elements, self.gaze_position
        # TODO gaze_elements can be none? hmm
        if gaze is None:
            pass  # might be an issue with the eyetracker... or it may be loading up

        # # TODO an option for this (its a timeout)
        # if self._missing_gaze_since > 1:
        #     raise ValueError(
        #         "Guidance agent has not recieved gaze input for more than 1 second.")

        # gaze_elements, gaze = self.gaze_at_elements, self.gaze_position
        # this is the last gaze timestamp, it should be relatively close to NOW, otherwise the eyetracker may not be functioning
        # gaze_timestamp = gaze['timestamp']  # TODO check this...

        # =================================================== #
        # here the agent is deciding whether to show guidance
        # it uses the same rules as icua version 1 (TODO grace period)
        # =================================================== #
        if self._guidance_on_task:
            # guidance is active, should it be?
            if self._is_task_acceptable[self._guidance_on_task]:
                # the task is now acceptable - hide guidance for this task
                self.hide_guidance(self._guidance_on_task)
            if self._guidance_on_task in gaze_elements:
                # turn off guidance, the user is looking at the task - hide guidance
                self.hide_guidance(self._guidance_on_task)
            else:
                # the user is not looking at the task and its unacceptable, keep guidance on.
                pass
        else:
            current_time = time.time()
            # guidance is not active, should it be?
            unacceptable = list(self._is_task_acceptable.items())
            # is the task in an unacceptable state? (remove if they are acceptable)
            unacceptable = [x[0] for x in unacceptable if not x[1]]
            # is the user looking at the task? (remove if they are)
            unacceptable = [x for x in unacceptable if x not in gaze_elements]
            # is the grace period over for the task?
            unacceptable = [
                x
                for x in unacceptable
                if current_time - self._guidance_last[x] > self._grace_period
            ]
            if len(unacceptable) > 0:
                # there are tasks in failure, decide which one to highlight
                # break ties randomly - this could be more interesting!
                task = self.break_guidance_tie(unacceptable, self._break_ties)
                self.show_guidance(task)  # show guidance on the chosen task
            else:
                pass  # no task is in failure, no guidance should be shown.

    def break_guidance_tie(self, tasks, method="random"):
        assert len(tasks) > 0
        if method == "random":
            # randomly break the tie
            return random.choice(tasks)
        elif method == "longest":
            return max(
                [(x, self._task_unacceptable_start[x]) for x in tasks],
                key=lambda x: x[1],
            )[0]
            # choose the one longest in failure
        elif method == "since":
            # choose the one with with the longest time since guidance was last shown
            return max(
                [(x, self._guidance_last[x]) for x in tasks], key=lambda x: x[1]
            )[0]
        else:
            raise ValueError(
                f"Unknown guidance tie break method: {self._break_ties}, must be one of {DefaultGuidanceAgent.BREAK_TIES}"
            )

    def on_acceptable(self, task: str):
        self._log(task, "acceptable", True)

    def on_active(self, task: str):
        self._log(task, "active", True)

    def on_unacceptable(self, task: str):
        # NOTE: this time is not the exact time that the task went into failure.
        # for this we would need to track the exact events that caused the failure, this is easier said than done...
        self._task_unacceptable_start[task] = time.time()
        self._log(task, "acceptable", False)

    def on_inactive(self, task: str):
        self._log(task, "active", False)
        self._task_inactive_start[task] = time.time()

    @observe([EyeMotionEvent, MouseMotionEvent])
    def _on_motion_event(self, event: MouseMotionEvent | EyeMotionEvent):
        """It may be useful to the actuators to get these events."""
        # TODO we may need to guard against actuators executing these actions...
        self.attempt(event)

    @property
    def guidance_actuators(self) -> list[GuidanceActuator]:
        """The guidance actuator used by this agent."""
        candidates = list(
            filter(lambda x: isinstance(x, GuidanceActuator), self.actuators)
        )
        if len(candidates) == 0:
            raise ValueError(
                f"Missing required actuator of type: `{GuidanceActuator.__qualname__}`"
            )
        return candidates
       

    def _log(self, task, z, ok):
        info = "task %20s %20s %s" % (z, task, ["✘", "✔"][int(ok)])
        LOGGER.info(info)
