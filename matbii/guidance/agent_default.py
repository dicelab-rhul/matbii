"""Module contains a default implementation for a guidance agent, see `DefaultGuidanceAgent` documentation for details."""

import random
from typing import Any, Literal
from collections.abc import Iterable
from star_ray.agent import Actuator, Sensor, observe
from icua.event import MouseMotionEvent, EyeMotionEvent
from icua.agent import (
    ArrowGuidanceActuator,
    BoxGuidanceActuator,
)
from icua.utils import LOGGER
from .agent_base import GuidanceAgent

__all__ = (
    "DefaultGuidanceAgent",
    "ArrowGuidanceActuator",
    "BoxGuidanceActuator",
)


class DefaultGuidanceAgent(GuidanceAgent):
    """Default implementation of a guidance agent for the matbii system.

    Show guidance if:
        1. there is no guidance already active.
        2. the task is unacceptable.
        3. the user is not already attending on the task.
        4. the grace period has elapsed.
    """

    # used to break ties when multiple tasks could be highlighted. See `break_tie` method.
    BREAK_TIES = ("random", "longest")

    # condition 4. - whether to track the time since the last failure, or since the last guidance was shown
    GRACE_ON = ("guidance_task", "guidance_any", "failure", "attention")

    # method to use to determine which task the user is attending to
    ATTENTION_MODES = ("fixation", "gaze", "mouse")

    # if we havent had fresh eyetracking data for more than this, there may be something wrong... display a warning
    MISSING_GAZE_DATA_THRESHOLD = 0.1

    def __init__(
        self,
        sensors: list[Sensor],
        actuators: list[Actuator],
        break_ties: Literal["random", "longest"] = "random",
        grace_mode: Literal[
            "guidance_task", "guidance_any", "failure", "attention"
        ] = "failure",
        attention_mode: Literal["fixation", "gaze", "mouse"] = "fixation",
        grace_period: float = 3.0,
        counter_factual: bool = False,
        **kwargs: dict[str, Any],
    ):
        """Constructor.

        Args:
            sensors (list[Sensor]): list of sensors, this will typically be a list of `icua.agent.TaskAcceptabilitySensor`s. A `UserInputSensor` will always be added automatically.
            actuators (list[Actuator]): list of actuators, this will typically contain actuators that are capable of providing visual feedback to a user, see e.g. `icua.agent.GuidanceActuator` and its concrete implementations. A `CounterFactualGuidanceActuator` will be added by default.
            break_ties (Literal["random", "longest", "since"], optional): how to break ties if guidance may be shown on multiple tasks simultaneously. Defaults to "random". "random" will randomly break the tie, "longest" will choose the task that has been in failure for the longest, "since" will choose the task that has not had guidance shown for the longest time.
            grace_mode (Literal["guidance_task", "guidance_any", "failure", "attention"], optional): how to track the grace period. "guidance_task" will track the time since guidance was last shown on the task, "guidance_any" will track the time since guidance was last shown on any task, "failure" will track the time since the last failure on the task, "attention" will track the time since the user was last attending to a task. Defaults to "failure".
            attention_mode (Literal["fixation", "gaze", "mouse"], optional): method of determining where the user is attending. "fixation" will use the most recent gaze fixation, "gaze" will use the gaze position (including saccades), "mouse" will use the current mouse position. Defaults to "fixation".
            grace_period (float, optional): the time to wait (seconds) before guidance may be shown for a task after the last time guidance was shown on the task. Defaults to 3.0 seconds.
            counter_factual (bool, optional): whether guidance should be shown to the user, or whether it should just be logged.  This allows counter-factual experiments to be run, we can track when guidance would have been shown, and compare the when it was actually shown (in a different run). Defaults to False.
            kwargs (dict[str,Any]): Additional optional keyword arguments.
        """
        super().__init__(
            list(filter(None, sensors)),
            list(filter(None, actuators)),
            counter_factual=counter_factual,
            **kwargs,
        )
        self._attention_mode = attention_mode
        if self._attention_mode not in DefaultGuidanceAgent.ATTENTION_MODES:
            raise ValueError(
                f"Invalid argument: `attention_mode` {self._attention_mode} must be one of {DefaultGuidanceAgent.ATTENTION_MODES}"
            )

        self._grace_mode = grace_mode
        if self._grace_mode not in DefaultGuidanceAgent.GRACE_ON:
            raise ValueError(
                f"Invalid argument: `grace_mode` {self._grace_mode} must be one of {DefaultGuidanceAgent.GRACE_ON}"
            )

        self._break_ties = break_ties
        if self._break_ties not in DefaultGuidanceAgent.BREAK_TIES:
            raise ValueError(
                f"Invalid argument: `break_ties` {self._break_ties} must be one of {DefaultGuidanceAgent.BREAK_TIES}"
            )

        self._grace_period = grace_period  # TODO
        if self._grace_period < 0.0:
            raise ValueError(
                f"Invalid argument: `grace_period` {self._grace_period} must be > 0 "
            )

        # used to track the tasks that the user is currently attending to
        self._attending_tasks = set()

    def on_attending(self, attending_tasks: set[str]) -> None:
        """Called when the user's attention changes.

        Args:
            attending_tasks (set[str]): the new set of tasks that the user is currently attending to.
        """
        for task in attending_tasks:
            self.beliefs[task]["last_attended"] = self.get_cycle_start()
            self._log_info(task, "attending", True)
        if len(attending_tasks) == 0:
            self._log_info("none", "attending", True)

    def decide(self):  # noqa
        # update when the user was last attending to a task
        attending_tasks = self.get_attending_tasks()  # empty or a single task
        if attending_tasks != self._attending_tasks:
            self._attending_tasks = attending_tasks
            self.on_attending(attending_tasks)

        # make guidance decisions
        if self.guidance_on_tasks:
            # guidance is active, should it be?
            guidance_and_acceptable = self.guidance_on_tasks & self.acceptable_tasks
            if guidance_and_acceptable:
                # the task has guidance showing, but is now acceptable - hide guidance for this task
                for task in guidance_and_acceptable:
                    self.hide_guidance(task)
                return

            guidance_and_attending = self.guidance_on_tasks & self._attending_tasks
            if guidance_and_attending:
                # the task has guidance showing, but the user is attending to it - hide guidance for this task
                for task in guidance_and_attending:
                    self.hide_guidance(task)
                return

            # keep showing guidance
        else:
            # guidance is NOT active, should it be?
            # these tasks are candidates for showing guidance
            unacceptable = self.unacceptable_tasks
            # remove those tasks that the user is currently attending
            unacceptable -= self._attending_tasks
            # check the grace period
            unacceptable = self.grace_period_over(unacceptable)

            task = self.break_tie(unacceptable)
            if task:
                # we have selected a task to show guidance on
                self.show_guidance(task)

            # no task meets the criteria, the user is doing well!

    def grace_period_over(self, tasks: set[str]) -> set[str]:
        """Get the set of (unacceptable) tasks that have had their grace period elapse.

        Args:
            tasks (set[str]): the set of tasks to check.

        Returns:
            set[str]: the set of tasks that have had their grace period elapse.
        """
        if self._grace_mode == "guidance_task":
            # how long since guidance was last shown on the task?
            def _grace_met(t):
                tsgs = self.time_since_guidance_start(t)
                # check if grace period has elapsed, or if guidance has never been shown on the task (NaN value)
                return tsgs > self._grace_period or tsgs != tsgs

            return set(t for t in tasks if _grace_met(t))
        elif self._grace_mode == "guidance_any":
            # how long since guidance was last shown on any task?
            tsgs = self.time_since_guidance_start(None)
            if tsgs > self._grace_period or tsgs != tsgs:
                return tasks  # guidance has not been shown recently
            else:
                return set()  # a task has recently had guidance shown, we should not show guidance for any task yet
        elif self._grace_mode == "attention":

            def _grace_met(t):
                tsgs = self.time_since_last_attended(t)
                # check if grace period has elapsed, or if guidance has never been shown on the task (NaN value)
                return tsgs > self._grace_period or tsgs != tsgs

            # print({t: (_grace_met(t), self.time_since_last_attended(t)) for t in tasks})
            # how long since the user was last attending to a task?
            return set(t for t in tasks if _grace_met(t))
        elif self._grace_mode == "failure":
            # how long has this task been in failure?
            return set(
                t
                for t in tasks
                if self.time_since_failure_start(t) > self._grace_period
            )
        else:
            raise ValueError(
                f"Unknown grace mode: {self._grace_mode}, must be one of {DefaultGuidanceAgent.GRACE_ON}"
            )

    def time_since_last_attended(self, task: str) -> float:
        """Get the time since the user was last attending to a task."""
        return self.get_cycle_start() - self.beliefs[task].get(
            "last_attended", float("nan")
        )

    def get_attending_tasks(self) -> set[str]:
        """Get the set of tasks that the user is currently attending to - this is typically only one task.

        Returns:
            set[str]: set of tasks that the user is currently attending to (empty if no tasks are being attended to).
        """
        if self._attention_mode == "fixation":
            result = self.attending_task_fixation()
        elif self._attention_mode == "gaze":
            result = self.attending_task_gaze()
        elif self._attention_mode == "mouse":
            result = self.attending_task_mouse()
        else:
            raise ValueError(f"Unknown attention mode: {self._attention_mode}")
        if result is None:
            return set()
        else:
            return set([result])

    def attending_task_mouse(self) -> str | None:
        """Use mouse position to determine which task the user is attending to."""
        return self.mouse_target

    def attending_task_gaze(self) -> str | None:
        """Use gaze position (including saccades) to determine which task the user is attending to."""
        return self.gaze_target

    def attending_task_fixation(self) -> str | None:
        """Use fixation to determine which task the user is attending to."""
        #print(self.fixation_target)
        return self.fixation_target

    def break_tie(
        self,
        tasks: Iterable[str],
        method: Literal["random", "longest"] = "random",
    ) -> str | None:
        """Break a tie on tasks that all met the criteria for displaying guiance.

        The tie is broken using the `method` argument:
        - "random" will randomly break the tie.
        - "longest" will choose the task that has been in failure for the longest.

        Args:
            tasks (Iterable[str]): tasks to break the tie, one of which will be returned.
            method (Literal["random", "longest"], optional): how to break ties if guidance may be shown on multiple tasks simultaneously. Defaults to "random".

        Returns:
            str: the chosen task, or None if there are no tasks to choose from.
        """
        if len(tasks) == 0:
            return None
        if method == "random":
            # randomly break the tie
            return random.choice(list(tasks))
        elif method == "longest":
            # choose the task longest in failure
            return max(
                [(task, self.time_since_failure_start(task)) for task in tasks],
                key=lambda x: x[1],
            )[0]
        else:
            raise ValueError(
                f"Unknown guidance tie break method: {method}, must be one of {DefaultGuidanceAgent.BREAK_TIES}"
            )

    @observe([EyeMotionEvent, MouseMotionEvent])
    def _on_motion_event(self, event: MouseMotionEvent | EyeMotionEvent):
        """It may be useful to the actuators to get these events. It is a trick to forward sensory input to the agents actuators. The `ArrowGuidanceActuator` is an example that requires this information to display the array at the gaze/mouse position."""
        # TODO we may need to guard against actuators executing these actions...?
        # manually attempt the event, we could specify which actuators need this information...?
        self.attempt(event)

    def on_acceptable(self, task: str):  # noqa
        self._log_info(task, "acceptable", True)
        return super().on_acceptable(task)

    def on_unacceptable(self, task: str):  # noqa
        self._log_info(task, "acceptable", False)
        return super().on_unacceptable(task)

    def _log_info(self, task, z, ok):
        """Log info related to a task to the console."""
        info = "task %20s %20s %s" % (z, task, ["✘", "✔"][int(ok)])
        LOGGER.info(info)
