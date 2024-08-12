"""Module that implements the "tracking" task.

This files contains:
    - avatar actuator: `AvatarTrackingActuator`
    - agent actuator: `TrackingActuator`
    - actions: [`TargetMoveAction`]
"""

import math
import random
import time
from typing import Any
from pydantic import field_validator

from star_ray_xml import XMLState, Expr, update, select
from icua.event import KeyEvent, XMLUpdateQuery
from icua.utils import LOGGER
from icua.agent import Actuator, attempt

from ...utils._const import DEFAULT_KEY_BINDING  # TODO support other key bindings?

__all__ = ("AvatarTrackingActuator", "TrackingActuator", "TargetMoveAction")

DIRECTION_MAP = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}


class AvatarTrackingActuator(Actuator):
    """Actuator class that should be added to the Avatar when the tracking task is enabled. It allows the user to control the "target" in this task."""

    def __init__(
        self, target_speed: float = 5.0, *args: list[Any], **kwargs: dict[str, Any]
    ):
        """Constructor.

        Args:
            target_speed (float): the speed of the target (svg units per second).
            args (list[Any], optional): additional optional arguments.
            kwargs (dict[Any], optional): additional optional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self._keys_pressed = set()
        self._prev_time = time.time()
        self._target_speed = target_speed

    def __attempt__(self) -> list["TargetMoveAction"]:
        """Attempt method that will attempt a `TargetMoveAction` to move the target according to the users input (if it has been provided since the last call to this method).

        Returns:
            list[TargetMoveAction]: the action
        """
        current_time = time.time()
        # this will contain the user action (KeyEvent)
        actions = []
        if len(self._keys_pressed) > 0:
            # compute speed based on time that has passed
            dt = current_time - self._prev_time
            speed = self._target_speed * dt
            # this will be normalised when the action is executed
            result = [0, 0]
            # compute the movement action based on the currently pressed keys
            for key in self._keys_pressed:
                direction = DIRECTION_MAP[DEFAULT_KEY_BINDING[key]]
                result[0] += direction[0]
                result[1] += direction[1]
            if result[0] != 0 or result[1] != 0:
                actions.append(TargetMoveAction(direction=tuple(result), speed=speed))
        self._prev_time = current_time
        return actions

    @attempt
    def attempt_key_event(self, user_action: KeyEvent) -> list:
        """Attempt method that takes a `KeyEvent` as input from the user. It is up to the avatar to provide this event to this actuator. The information is essential if the user is to control this task.

        Args:
            user_action (KeyEvent): the users keyboard action

        Returns:
            list: an empty list (no action is taken by this attempt method, see `AvatarTrackingActuator.__attempt__`.
        """
        if user_action.key.lower() in DEFAULT_KEY_BINDING:
            if user_action.status == KeyEvent.UP:
                self._keys_pressed.remove(user_action.key)
            elif user_action.status in (KeyEvent.DOWN, KeyEvent.HOLD):
                self._keys_pressed.add(user_action.key)
        return []

    # @attempt
    # def attempt_joystick_event(self, user_action: JoyStickEvent):
    #     # TODO If a joystick device is used (and supported elsewhere), this is where we would handle the action.
    #     # the handling should look similar to key events above but might require some work (if the input is continuous for example)
    #     raise NotImplementedError()


class TrackingActuator(Actuator):
    """Actuator class that will be part of a `ScheduledAgent` or any other agent that controls the evolution of the tracking task."""

    @attempt
    def move_target(
        self, direction: tuple[float, float] | int | float, speed: float
    ) -> "TargetMoveAction":
        """Move the tracking target in a given direction at a given speed.

        Args:
            direction (tuple[float, float] | int | float): direction to move.
            speed (float): speed to move (svg units per call to this function) # TODO perhaps this should be per second!

        Returns:
            TargetMoveAction: the action to move the tracking target.
        """
        # an angle was provided (in degrees), convert it to a direction vector
        if isinstance(direction, int | float):
            angle = math.radians(direction)
            direction = (math.sin(angle), math.cos(angle))
        return TargetMoveAction(direction=direction, speed=speed)

    @attempt
    def perturb_target(self, speed: float) -> "TargetMoveAction":
        """Move the tracking target in a random direction at a given speed.

        Args:
            speed (float): speed to move (svg units per call to this function) # TODO perhaps this should be per second!

        Returns:
            TargetMoveAction: the action to move the tracking target.
        """
        angle = (random.random() * 2 - 1) * math.pi
        direction = (math.sin(angle), math.cos(angle))
        return TargetMoveAction(direction=direction, speed=speed)


class TargetMoveAction(XMLUpdateQuery):
    """Action class that will update the tracking target position."""

    direction: tuple[float, float]
    speed: float

    @field_validator("direction", mode="before")
    @classmethod
    def _validate_direction(cls, value):
        if isinstance(value, list):
            value = tuple(value)  # a list is ok, convert it to a tuple
        if isinstance(value, tuple):
            if len(value) == 2:
                # normalise the direction
                d = math.sqrt(value[0] ** 2 + value[1] ** 2)
                if d == 0:
                    return (0.0, 0.0)
                return (float(value[0]) / d, float(value[1]) / d)
        raise ValueError(f"Invalid direction {value}, must be Tuple[float,float].")

    @field_validator("speed", mode="before")
    @classmethod
    def _validate_speed(cls, value):
        return float(value)

    def __execute__(self, state: XMLState):  # noqa
        if self.direction == (0.0, 0.0):
            LOGGER.warning(
                f"Attempted {TargetMoveAction.__name__} with direction (0,0)",
            )
            return
        dx = self.direction[0] * self.speed
        dy = self.direction[1] * self.speed
        # get properties of the tracking task
        properties = state.select(
            select(
                xpath="//svg:svg/svg:svg[@id='tracking']",
                attrs=["width", "height"],
            )
        )[0]
        # task bounds should limit the new position
        x1, y1 = (0.0, 0.0)
        x2, y2 = x1 + properties["width"], y1 + properties["height"]

        new_x = Expr("max(min({x} + {dx}, {x2} - {width}), {x1})", dx=dx, x1=x1, x2=x2)
        new_y = Expr("max(min({y} + {dy}, {y2} - {height}), {y1})", dy=dy, y1=x1, y2=y2)
        return state.update(
            update(
                xpath="//svg:svg/svg:svg/svg:svg[@id='tracking_target']",
                attrs=dict(x=new_x, y=new_y),
            )
        )
