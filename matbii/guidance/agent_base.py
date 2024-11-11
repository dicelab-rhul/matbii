"""Module containing the base class for matbii guidance agents, see `GuidanceAgent` documentation for details."""

from typing import Any
import time
from icua.agent.actuator_guidance import (
    CounterFactualGuidanceActuator,
)
from icua.event import (
    Event,
    EyeMotionEvent,
    MouseMotionEvent,
)
from icua.agent import GuidanceAgent as _GuidanceAgent
from icua.extras.logging import LogActuator
from icua.utils import LOGGER  # , dict_diff

from star_ray.agent import Actuator, Sensor


class GuidanceAgent(_GuidanceAgent):
    """Base class for matbii guidance agents.

    This class adds some useful fields to the the `beliefs` dict.
    - `is_guidance`: whether guidance is currently being shown for the task.
    - `failure_start`: the time since the last failure started on the task.
    - `guidance_start`: the time since the last guidance started to be shown on the task.

    Other fields are inherited:
    - `is_acceptable`: whether the task is currently acceptable.
    - `is_active`: whether the task is currently active.

    All of these fields are accessible via the corresponding task keys, e.g. `self.beliefs[task]["is_guidance"]`.
    They are updated internally as new observations are received (or actions are taken), it is best not to assign to these fields directly.
    """

    def __init__(  # noqa inherited docs
        self,
        sensors: list[Sensor],
        actuators: list[Actuator],
        counter_factual: bool = False,
        user_input_events: tuple[type[Event]] = None,
        user_input_events_history_size: int | list[int] = 50,
    ):
        # this actuator will be used when counter-factual guidance is enabled, any other actuators will be ignored
        _counter_factual_guidance_actuator = CounterFactualGuidanceActuator()
        actuators.append(_counter_factual_guidance_actuator)
        super().__init__(
            sensors, actuators, user_input_events, user_input_events_history_size
        )
        self._counter_factual = counter_factual
        self._counter_factual_guidance_actuator = _counter_factual_guidance_actuator

        # # these are used to look at differences in beliefs for logging purposes, old beliefs are copied at the end of each cycle (see __execute__)
        # self._old_beliefs = deepcopy(self.beliefs)

        # various useful properties used to determine whether guidance should be shown
        self._cycle_start_time = None

    def show_guidance(self, task: str):
        """Show guidance for a given task.

        If overriding you must call super() to ensure consistent behaviour.

        Args:
            task (str): the task to show guidance for.
        """
        self.beliefs[task]["is_guidance"] = True
        self.beliefs[task]["guidance_start"] = self._cycle_start_time
        if not self._counter_factual:
            for actuator in self.guidance_actuators:
                actuator.show_guidance(task=task)
        else:
            self._counter_factual_guidance_actuator.show_guidance(task=task)

    def hide_guidance(self, task: str):
        """Hide guidance for a given task.

        If overriding you must call super() to ensure consistent behaviour.

        Args:
            task (str): the task(s) to hide guidance for.
        """
        self.beliefs[task]["is_guidance"] = False
        if not self._counter_factual:
            for actuator in self.guidance_actuators:
                actuator.hide_guidance(task=task)
        else:
            self._counter_factual_guidance_actuator.hide_guidance(task=task)

    def log_belief(self, belief: dict[str, Any] | Event) -> None:
        """Method that is intended for logging the beliefs of this agent to a file. This can be very useful for keeping track of the state of the simulation, user input, task acceptability and guidance for post analysis purposes.

        Requires `icua.extras.logging.LogActuator` be attached to this agent and will otherwise have no effect. Logging can be configured in the `LogActuator`, including the way that beliefs are formatted in the file.

        Note that the belief wont be logged immediately, but will be buffered as an action and logged as part of usual action execution cycle (on execute).

        Args:
            belief (dict[str, Any]): belief to log
        """
        actuator: LogActuator | None = next(
            iter(self.get_actuators(oftype=LogActuator)), None
        )
        if actuator:
            actuator.log(belief)
        else:
            LOGGER.warning(
                "Attempted to log a belief without the required actuator: `icua.extras.logging.LogActuator`"
            )

    def __cycle__(self):  # noqa
        self._cycle_start_time = time.time()
        super().__observe__()
        self.decide()
        self.__decide__()

    # def __execute__(self, state: State, *args, **kwargs):  # noqa
    #     # always call this at the end of the cycle (when all beliefs have been updated in subclass)
    #     diff = dict_diff(self._old_beliefs, self.beliefs)
    #     if diff:
    #         # there were some updates to the beliefs, log them and update old beliefs to reflect these changes
    #         self.log_belief(self.beliefs)  # differences in beliefs
    #         self._old_beliefs = deepcopy(self.beliefs)
    #         # print(diff)

    #     # t = time.time()
    #     # print(t - self._timestamp)
    #     # self._timestamp = t
    #     super().__execute__(state, *args, **kwargs)

    def decide(self):
        """Decide method for this agent. This method is intended to determine the guidance actions the agent will take in each cycle. Make use of the `show_guidance` and `hide_guidance` methods to control guidance rather than using raw actions or attempt methods. This will ensure consistent behaviour and handle possible counter-factual guidance."""
        raise NotImplementedError(
            f"Subclasses of {GuidanceAgent.__module__}.{GuidanceAgent.__name__} must implement the `decide` method, this method is intended to determine the guidance actions the agent will take in each cycle."
        )

    # this is manually added to the event router (see __init__), so no @observe here
    def on_user_input(self, observation: Event):
        """Called when this agent receives a user input event, it will add the event to an internal buffer. See `get_latest_user_input`.

        This method should not be called manually and will be handled by this agents event routing mechanism.

        Args:
            observation (Any): the observation.
        """
        super().on_user_input(observation)
        # TODO may move this into `log_beliefs` and just use the event buffer.
        # log all user input events as beliefs
        # self.log_belief(observation)

    # ================================================================================================ #
    # ================================ Below are some useful methods ================================= #
    # ================================================================================================ #

    def time_since_failure_start(self, task: str | None = None) -> float:
        """Get the time since the last failure started on the task (or any task if `task` is None).

        Args:
            task (str | None): the task. If None, use any task.

        Returns:
            float: the time since the last failure started on the task (or any task if `task` is None).
        """
        if task is None:
            failure_time = max(
                self.beliefs[task].get("failure_start", float("nan"))
                for task in self.monitoring_tasks
            )
        else:
            failure_time = self.beliefs[task].get("failure_start", float("nan"))
        return self._cycle_start_time - failure_time

    def time_since_guidance_start(self, task: str | None = None) -> float:
        """Get the time since the last guidance started to be shown on the task (or any task if `task` is None).

        Args:
            task (str | None): the task. If None, use any task.

        Returns:
            float: the time since the last guidance started to be shown on the task (or any task if `task` is None).
        """
        if task is None:
            guidance_time = max(
                self.beliefs[task].get("guidance_start", float("nan"))
                for task in self.monitoring_tasks
            )
        else:
            guidance_time = self.beliefs[task].get("guidance_start", float("nan"))
        return self._cycle_start_time - guidance_time

    # ================================================================================================ #
    # =============================== Below are some useful properties =============================== #
    # ================================================================================================ #

    @property
    def guidance_on_tasks(self) -> set[str]:
        """Get the set of tasks that guidance is currently being shown on.

        Returns:
            set[str]: set of tasks that guidance is currently being shown on.
        """
        return set(
            t for t in self.active_tasks if self.beliefs[t].get("is_guidance", False)
        )

    def on_unacceptable(self, task: str):  # noqa
        self.beliefs[task]["failure_start"] = self._cycle_start_time
        return super().on_unacceptable(task)

    @property
    def mouse_target(self) -> str | None:
        """Get the task that the mouse is currently over."""
        event: MouseMotionEvent | None = next(
            self.get_latest_user_input(MouseMotionEvent), None
        )
        if event is None:
            return None
        targets = set(event.target) & self.monitoring_tasks
        return next(iter(targets), None)

    @property
    def gaze_target(self) -> str | None:
        """Get the task that the gaze is currently over."""
        event: EyeMotionEvent | None = next(
            self.get_latest_user_input(EyeMotionEvent), None
        )
        if event is None:
            return None
        targets = set(event.target) & self.monitoring_tasks
        return next(iter(targets), None)
