"""Module contains a default implementation for a guidance agent, see `DefaultGuidanceAgent` documentation for details."""

import time
import random
from typing import Any, Literal
from star_ray.agent import Actuator, Sensor, observe
from icua.event import MouseMotionEvent, EyeMotionEvent
from icua.agent import (
    GuidanceActuator,
    CounterFactualGuidanceActuator,
    ArrowGuidanceActuator,
    BoxGuidanceActuator,
    TaskAcceptabilitySensor,
)
from icua.utils import LOGGER
from star_ray.environment import State  # type hint
from .agent_base import GuidanceAgent

__all__ = (
    "DefaultGuidanceAgent",
    "ArrowGuidanceActuator",
    "BoxGuidanceActuator",
)


class DefaultGuidanceAgent(GuidanceAgent):
    """Default implementation of a guidance agent for the matbii system.

    TODO document
    """

    # used to break ties when multiple tasks could be highlighted. See `break_guidance_tie` method below.
    BREAK_TIES = ("random", "longest", "since")

    # if we havent had fresh eyetracking data for more than this, there may be something wrong... display a warning
    MISSING_GAZE_DATA_THRESHOLD = 0.1

    def __init__(
        self,
        sensors: list[Sensor],
        actuators: list[Actuator],
        break_ties: Literal["random", "longest", "since"] = "random",
        attention_mode: Literal["gaze", "mouse"] = "mouse",
        grace_period: float = 3.0,
        counter_factual: bool = False,
        **kwargs: dict[str, Any],
    ):
        """Constructor.

        Args:
            sensors (list[Sensor]): list of sensors, this will typically be a list of `icua.agent.TaskAcceptabilitySensor`s. A `UserInputSensor` will always be added automatically.
            actuators (list[Actuator]): list of actuators, this will typically contain actuators that are capable of providing visual feedback to a user, see e.g. `icua.agent.GuidanceActuator` and its concrete implementations. A `CounterFactualGuidanceActuator` will be added by default.
            break_ties (Literal["random", "longest", "since"], optional): how to break ties if guidance may be shown on multiple tasks simultaneously. Defaults to "random". "random" will randomly break the tie, "longest" will choose the task that has been in failure for the longest, "since" will choose the task that has not had guidance shown for the longest time.
            attention_mode (Literal["gaze", "mouse"], optional): method of determining where the user is paying attention. "mouse" will track the mouse position, "gaze" will track the gaze position (if avaliable). Defaults to "mouse".
            grace_period (float, optional): the time to wait (seconds) before guidance may be shown for a task after the last time guidance was shown on the task. Defaults to 3.0 seconds.
            counter_factual (bool, optional): whether guidance should be shown to the user, or whether it should just be logged.  This allows counter-factual experiments to be run, we can track when guidance would have been shown, and compare the when it was actually shown (in a different run). Defaults to False.
            kwargs (dict[str,Any]): Additional optional keyword arguments.
        """
        _counter_factual_guidance_actuator = CounterFactualGuidanceActuator()
        actuators.append(_counter_factual_guidance_actuator)
        super().__init__(sensors, actuators, **kwargs)

        # this agent is tracking the following tasks (based on the provided sensors)
        self._tracking_tasks = [s.task_name for s in self.task_acceptability_sensors]
        # initialise beliefs (empty)
        for task in self._tracking_tasks:
            self.beliefs[task] = dict(guidance=False)
        # also record some attention information (for logging)
        self.beliefs["attention"] = dict()

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
        self._counter_factual_guidance_actuator = _counter_factual_guidance_actuator
        self._attention_mode = attention_mode

    def __initialise__(self, state: State):  # noqa
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
        self.beliefs[task]["guidance"] = True
        if not self._counter_factual:
            for actuator in self.guidance_actuators:
                actuator.show_guidance(task=task)
        else:
            self._counter_factual_guidance_actuator.show_guidance(task=task)

    def hide_guidance(self, task: str):
        """Hide guidance for a given task.

        If overriding you must call super() to ensure consistent behaviour.

        Args:
            task (str): the task to hide guidance for.
        """
        if self._guidance_on_task:
            self.beliefs[self._guidance_on_task]["guidance"] = False
        self._guidance_on_task = None
        if not self._counter_factual:
            for actuator in self.guidance_actuators:
                actuator.hide_guidance(task=task)
        else:
            self._counter_factual_guidance_actuator.hide_guidance(task=task)

        # update the last time guidance was shown for the given task (for the grace period check)
        self._guidance_last[task] = time.time()

    def get_inactive_tasks(self) -> set[str]:
        """Get the set of inactive tasks.

        Returns:
            set[str]: set of inactive tasks.
        """
        active = list(self._is_task_active.items())
        return set([x[0] for x in active if not x[1]])

    def get_unacceptable_tasks(self) -> set[str]:
        """Get the set of unacceptable tasks.

        Returns:
            set[str]: set of unacceptable tasks.
        """
        unacceptable = list(self._is_task_acceptable.items())
        # is the task in an unacceptable state? (remove if they are acceptable)
        unacceptable = set([x[0] for x in unacceptable if not x[1]])
        # remove all inactive tasks (never display guidance for these)
        unacceptable -= self.get_inactive_tasks()
        return unacceptable

    def get_attending(self):
        """Get attention data from mouse or eyetracker."""
        if self._attention_mode == "gaze":
            elements, gaze = self.gaze_at_elements, self.gaze_position
            # check if the gaze data is None, if so we need to see how long and give a warning, it may indicate that the eyetracker
            # has stopped functioning which may invalidate an experimental trial!
            if gaze is None:
                if self._missing_gaze_since is None:
                    self._missing_gaze_since = time.time()
                elif (
                    time.time() - self._missing_gaze_since
                    > DefaultGuidanceAgent.MISSING_GAZE_DATA_THRESHOLD
                ):
                    LOGGER.warning(
                        f"No fresh gaze data for longer than: { DefaultGuidanceAgent.MISSING_GAZE_DATA_THRESHOLD}s"
                    )
                return {"elements": elements}
            else:
                self._missing_gaze_since = None
            # gaze data may be present, but it may be old (its stored in a buffer until fresh data arrives)
            if (
                time.time() - gaze["timestamp"]
                > DefaultGuidanceAgent.MISSING_GAZE_DATA_THRESHOLD
            ):
                LOGGER.warning(
                    f"No fresh gaze data for longer than: { DefaultGuidanceAgent.MISSING_GAZE_DATA_THRESHOLD}s"
                )
            return {"elements": elements, **(gaze if gaze else {})}
        elif self._attention_mode == "mouse":
            position_data = self.mouse_position
            return {
                "elements": self.mouse_at_elements,
                **(position_data if position_data else {}),
            }
        else:
            raise ValueError(f"Unknown attention mode: {self._attention_mode}")

    def __cycle__(self):  # noqa
        super().__cycle__()
        attending = self.get_attending()
        att_to = attending["elements"]

        # TODO we might also care about recording other info in the event!
        # this is the one that is being used by the agent to make its guidance decisions either way...
        self.beliefs["attention"]["timestamp"] = attending.get("timestamp")
        self.beliefs["attention"]["position"] = attending.get("position")
        self.beliefs["attention"]["attending"] = next(
            iter([e for e in att_to if e in self._tracking_tasks]), None
        )

        # =================================================== #
        # here the agent is deciding whether to show guidance
        # it uses the same rules as icua version 1 (TODO check this)
        # =================================================== #
        if self._guidance_on_task:
            # guidance is active, should it be?
            if self._is_task_acceptable[self._guidance_on_task]:
                # the task is now acceptable - hide guidance for this task
                self.hide_guidance(self._guidance_on_task)
            if self._guidance_on_task in att_to:
                # turn off guidance, the user is looking at the task - hide guidance
                self.hide_guidance(self._guidance_on_task)
            else:
                # the user is not looking at the task and its unacceptable, keep guidance on.
                pass
        else:
            current_time = time.time()
            # guidance is not active, should it be?
            unacceptable = self.get_unacceptable_tasks()
            # is the user looking at the task? (remove if they are)
            unacceptable = [x for x in unacceptable if x not in att_to]
            # is the grace period over for the task?
            unacceptable = [
                x
                for x in unacceptable
                if current_time - self._guidance_last[x] > self._grace_period
            ]
            if len(unacceptable) > 0:
                # there are tasks in failure, decide which one to highlight
                task = self.break_guidance_tie(unacceptable, self._break_ties)
                self.show_guidance(task)  # show guidance on the chosen task
            else:
                pass  # no task is in failure, no guidance should be shown.

    def break_guidance_tie(
        self, tasks: list[str], method: Literal["random", "longest", "since"] = "random"
    ) -> str:
        """Break a tie on tasks that all met the criteria for displaying guiance.

        Args:
            tasks (list[str]): tasks to break the tie, one of which will be returned.
            method (Literal["random", "longest", "since"], optional): how to break ties if guidance may be shown on multiple tasks simultaneously. Defaults to "random". "random" will randomly break the tie, "longest" will choose the task that has been in failure for the longest, "since" will choose the task that has not had guidance shown for the longest.

        Returns:
            str: the chosen task.
        """
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

    def on_acceptable(self, task: str):  # noqa
        self.beliefs[task]["acceptable"] = True
        self._log_acceptability(task, "acceptable", True)

    def on_active(self, task: str):  # noqa
        self.beliefs[task]["active"] = True

        self._log_acceptability(task, "active", True)

    def on_unacceptable(self, task: str):  # noqa
        # NOTE: this time is not the exact time that the task went into failure.
        # for this we would need to track the exact events that caused the failure, this is easier said than done...
        self.beliefs[task]["acceptable"] = False

        self._task_unacceptable_start[task] = time.time()
        self._log_acceptability(task, "acceptable", False)

    def on_inactive(self, task: str):  # noqa
        self.beliefs[task]["active"] = False
        self._task_inactive_start[task] = time.time()

        self._log_acceptability(task, "active", False)

    @observe([EyeMotionEvent, MouseMotionEvent])
    def _on_motion_event(self, event: MouseMotionEvent | EyeMotionEvent):
        """It may be useful to the actuators to get these events. It is a trick to forward sensory input to the agents actuators. The `ArrowGuidanceActuator` is an example that requires this information to display the array at the gaze/mouse position."""
        # TODO we may need to guard against actuators executing these actions...?
        # manually attempt the event, we could specify which actuators need this information...?
        self.attempt(event)

    @property
    def task_acceptability_sensors(self) -> list[TaskAcceptabilitySensor]:
        """Getter for task acceptability sensors (sensors that derive the type: `icua.agent.TaskAcceptabilitySensor`).

        Returns:
            list[TaskAcceptabilitySensor]: the sensors.
        """
        return list(self.get_sensors(oftype=TaskAcceptabilitySensor))

    @property
    def guidance_actuators(self) -> list[GuidanceActuator]:
        """Getter for guidance actuators (actuators that derive the type: `icua.agent.GuidanceActuator`).

        Returns:
            list[GuidanceActuator]: the GuidanceActuator.
        """
        candidates = list(self.get_actuators(oftype=GuidanceActuator))
        if len(candidates) == 0:
            raise ValueError(
                f"Missing required actuator of type: `{GuidanceActuator.__qualname__}`"
            )
        return candidates

    def _log_acceptability(self, task, z, ok):
        info = "task %20s %20s %s" % (z, task, ["✘", "✔"][int(ok)])
        LOGGER.info(info)
