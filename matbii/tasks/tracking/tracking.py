import math
import random
import time
from pydantic import field_validator

from star_ray_xml import XMLState, Expr, update, select
from icua.event import KeyEvent, XMLUpdateQuery
from icua.utils import LOGGER
from icua.agent import Actuator, attempt


from ..._const import DEFAULT_KEY_BINDING  # TODO support other key bindings?

DIRECTION_MAP = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}
# TODO this should be set in a config somewhere
# this is measured in units per second and will be approximated based on the cycle time in TrackingActuator
DEFAULT_TARGET_SPEED = 100


class AvatarTrackingActuator(Actuator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._keys_pressed = set()
        self._prev_time = time.time()

    def __attempt__(self):
        current_time = time.time()
        # this will contain the user action (KeyEvent)
        actions = []
        if len(self._keys_pressed) > 0:
            # compute speed based on time that has passed
            dt = current_time - self._prev_time
            speed = DEFAULT_TARGET_SPEED * dt
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
    def attempt_key_event(self, user_action: KeyEvent):
        if user_action.key.lower() in DEFAULT_KEY_BINDING:
            if user_action.status == KeyEvent.UP:
                self._keys_pressed.remove(user_action.key)
            elif user_action.status in (KeyEvent.DOWN, KeyEvent.HOLD):
                self._keys_pressed.add(user_action.key)
        return []  # these will be recorded by the DefaultActuator

    # @attempt
    # def attempt_joystick_event(self, user_action: JoyStickEvent):
    #     # TODO If a joystick device is used (and supported elsewhere), this is where we would handle the action.
    #     # the handling should look similar to key events above but might require some work (if the input is continuous for example)
    #     raise NotImplementedError()


class TrackingActuator(Actuator):
    @attempt
    def move_target(self, direction: tuple[float, float] | int | float, speed: float):
        """Move the target in a given direction at a given speed."""
        # an angle was provided (in degrees), convert it to a direction vector
        if isinstance(direction, (int, float)):
            angle = math.radians(direction)
            direction = (math.sin(angle), math.cos(angle))
        return TargetMoveAction(direction=direction, speed=speed)

    @attempt
    def perturb_target(self, speed: float):
        """Perturb the target in a random direction at a given speed."""
        angle = (random.random() * 2 - 1) * math.pi
        direction = (math.sin(angle), math.cos(angle))
        return TargetMoveAction(direction=direction, speed=speed)


# TODO ??
class TrackingModeAction(XMLUpdateQuery):
    manual: bool


class TargetMoveAction(XMLUpdateQuery):
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

    def __execute__(self, state: XMLState):
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
    
   

