"""Module containing the base class for matbii guidance agents, see `GuidanceAgent` documentation for details."""

from typing import Any
from copy import deepcopy
from icua.event import Event, EyeMotionEvent, MouseMotionEvent
from icua.agent import GuidanceAgent as _GuidanceAgent
from icua.extras.eyetracking import EyetrackerIOSensor
from icua.extras.logging import LogActuator
from icua.utils import LOGGER, dict_diff

from star_ray.agent import Actuator, Sensor
from star_ray.environment import State


class GuidanceAgent(_GuidanceAgent):
    """Base class for matbii guidance agents.

    This class implements belief logging, assuming it has an attached `LogActuator`. Any updates to beliefs are logged by the actuator at the end of each cycle (during __execute__). This information, along with the raw event logs can be used for post-experiment analysis. Working with the guidance agent's beliefs may be easier than with the raw event logs as they contain relevant guidance & task acceptability info and custom data can be added in any subclass (simply by updating `self.beliefs`).
    """

    def __init__(  # noqa inherited docs
        self,
        sensors: list[Sensor],
        actuators: list[Actuator],
        user_input_events: tuple[type[Event]] = None,
        user_input_events_history_size: int | list[int] = 50,
    ):
        super().__init__(
            sensors, actuators, user_input_events, user_input_events_history_size
        )
        # these are used to look at differences in beliefs for logging purposes, old beliefs are copied at the end of each cycle (see __execute__)
        self._old_beliefs = deepcopy(self.beliefs)

    def log_belief(self, belief: dict[str, Any] | Event) -> None:
        """Method that is intended for logging the beliefs of this agent to a file. This can be very useful for keeping track of the state of the simulation, user input, task acceptability and guidance for post analysis purposes.

        Requires `icua.extras.logging.LogActuator` be attached to this agent and will otherwise have no effect. Logging can be configured in the `LogActuator`, including the way that beliefs are formatted in the file.

        Note that the belief wont be logged immediately, but will be buffered as an action and logged as part of usual action execution cycle (on execute).

        Args:
            belief (dict[str, Any]): belief to log
        """
        actuator: LogActuator = next(iter(self.get_actuators(oftype=LogActuator)), None)
        if actuator:
            actuator.log(belief)
        else:
            LOGGER.warning(
                "Attempted to log a belief without the required actuator: `icua.extras.logging.LogActuator`"
            )

    def __execute__(self, state: State, *args, **kwargs):  # noqa
        # always call this at the end of the cycle (when all beliefs have been updated in subclass)
        diff = dict_diff(self._old_beliefs, self.beliefs)
        if diff:
            # there were some updates to the beliefs, log them and update old beliefs to reflect these changes
            self.log_belief(self.beliefs)  # differences in beliefs
            self._old_beliefs = deepcopy(self.beliefs)
            # print(diff)

        # t = time.time()
        # print(t - self._timestamp)
        # self._timestamp = t
        super().__execute__(state, *args, **kwargs)

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
    # =============================== Below are some useful properties =============================== #
    # ================================================================================================ #

    @property
    def has_eyetracker(self) -> bool:
        """Whether this agent has an attached `EyetrackerIOSensor`.

        Returns:
            bool: Whether this agent has an attached `EyetrackerIOSensor`
        """
        return len(self.get_sensors(oftype=EyetrackerIOSensor)) > 0

    @property
    def mouse_at_elements(self) -> list[str]:
        """Getter for the elements that the mouse pointer is currently over (according to this agents beliefs).

        Returns:
            List[str]: list of element ids that the mouse pointer is currently over.
        """
        try:
            return next(self.get_latest_user_input(MouseMotionEvent)).target
        except StopIteration:
            return []

    @property
    def mouse_position(self) -> dict[str, Any]:
        """Getter for the user's current mouse position (according to this agents beliefs).

        Returns:
            Dict[str, Any]: dict containing the `timestamp` and mouse `position` (in svg coordinate space).
        """
        try:
            event = next(self.get_latest_user_input(MouseMotionEvent))
            return dict(timestamp=event.timestamp, position=event.position)
        except StopIteration:
            return None

    @property
    def gaze_at_elements(self) -> list[str]:
        """Getter for the elements that the user is currently gazing at (according to this agents beliefs).

        Returns:
            List[str]: list of element id's that the user is currently gazing at.
        """
        try:
            return next(self.get_latest_user_input(EyeMotionEvent)).target
        except StopIteration:
            return []

    @property
    def gaze_position(self) -> dict[str, Any]:
        """Getter for the user's current gaze position (according to this agents beliefs).

        Returns:
            Dict[str, Any]: dict containing the `timestamp` and gaze `position` (in svg coordinate space).
        """
        try:
            event = next(self.get_latest_user_input(EyeMotionEvent))
            return dict(timestamp=event.timestamp, position=event.position)
        except StopIteration:
            return None
