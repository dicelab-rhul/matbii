"""Module containing the base class for matbii guidance agents, see `GuidanceAgent` documentation for details."""

from typing import Any
from collections import deque
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
        user_input_events_history_size: int | list[int] = 100,
        cycle_times_history_size: int = 10,
    ):
        # this actuator will be used when counter-factual guidance is enabled, any other actuators will be ignored
        _counter_factual_guidance_actuator = CounterFactualGuidanceActuator()
        actuators.append(_counter_factual_guidance_actuator)
        super().__init__(
            sensors, actuators, user_input_events, user_input_events_history_size
        )
        self._counter_factual = counter_factual
        self._counter_factual_guidance_actuator = _counter_factual_guidance_actuator

        # various useful properties used to determine whether guidance should be shown
        self._cycle_times = deque(maxlen=max(cycle_times_history_size, 10))

    def get_cycle_start(self, index: int = 0) -> float:
        """Get the time since the previous cycle started.

        An index of 0 indicates the start of the current cycle.
        If the index is greater than the current history size N (which may happen in the first N - 1 cycles) the oldest cycle time will be returned.

        Args:
            index (int): the index of the cycle to get the start time for.

        Returns:
            float: the time since the given cycle started.
        """
        if index >= self._cycle_times.maxlen:
            raise ValueError(
                f"Invalid argument: `index` {index} must be less than the cycle times history size {self._cycle_times.maxlen}, the can be increased by setting `cycle_times_history_size` in the constructor."
            )
        index = min(index, len(self._cycle_times) - 1)
        return self._cycle_times[index]

    def show_guidance(self, task: str):
        """Show guidance for a given task.

        If overriding you must call super() to ensure consistent behaviour.

        Args:
            task (str): the task to show guidance for.
        """
        self.beliefs[task]["is_guidance"] = True
        self.beliefs[task]["guidance_start"] = self.get_cycle_start()
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
        # add the latest cycle time (according to this agents cycle)
        self._cycle_times.appendleft(time.time())
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
        return self.get_cycle_start() - failure_time

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
        return self.get_cycle_start() - guidance_time

    def on_unacceptable(self, task: str):  # noqa
        self.beliefs[task]["failure_start"] = self.get_cycle_start()
        return super().on_unacceptable(task)

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

    @property
    def fixation_target(self) -> str | None:
        """Get the task that the user is currently fixating on. Eyetracking events arrive quickly, this will check events that have been generated since the last cycle of this agent.

        Returns:
            str | None: the task that the user is currently fixating on, or None if the user is not currently fixating on any task.
        """
        # gather events since the previous cycle
        latest_fixation: EyeMotionEvent | None = None
        # use events from the last 3 cycles, rather than the last cycle... this makes things a bit more robust with timings, 
        # especially if the fixation filter is not great (TODO we could choose different values or make this configurable...?)
        prev_cycle_start = self.get_cycle_start(3)
        _total = 0
        for event in self._user_input_events[EyeMotionEvent]:
            if event.timestamp >= prev_cycle_start:
                _total += 1
                if event.fixated:
                    latest_fixation = event
                    break  # found latest fixation
            else:
                break  # dont check older events
        #print(_total)
        if latest_fixation is None:
            return None
        targets = set(latest_fixation.target) & self.monitoring_tasks
        return next(iter(targets), None)

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
