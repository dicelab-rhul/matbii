import re
import time
from functools import partial

from star_ray.agent import Actuator, attempt
from star_ray.event import MouseButtonEvent, MouseMotionEvent, KeyEvent, JoyStickEvent
from ...action import (
    TargetMoveAction,
    ToggleLightAction,
    TogglePumpAction,
    ResetSliderAction,
)

from ...utils import DEFAULT_KEY_BINDING  # TODO support other key bindings?

DIRECTION_MAP = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}
# TODO this should be set in a config somewhere
# this is measured in units per second and will be approximated based on the cycle time in TrackingActuator
DEFAULT_TARGET_SPEED = 100


class TrackingActuator(Actuator):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._keys_pressed = set()
        self._prev_time = time.time()

    def __attempt__(self):
        current_time = time.time()
        # this will contain the user action (KeyEvent)
        actions = list(self.iter_actions())
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

    @attempt(route_events=[KeyEvent])
    def attempt_key_event(self, user_action: KeyEvent):
        if user_action.key in DEFAULT_KEY_BINDING:
            if user_action.status == KeyEvent.UP:
                self._keys_pressed.remove(user_action.key)
            elif user_action.status in (KeyEvent.DOWN, KeyEvent.HOLD):
                self._keys_pressed.add(user_action.key)
        return [user_action]

    @attempt(route_events=[JoyStickEvent])
    def attempt_joystick_event(self, user_action: JoyStickEvent):
        # TODO If a joystick device is used (and supported elsewhere), this is where we would handle the action.
        # the handling should look similar to key events above but might require some work (if the input is continuous for example)
        raise NotImplementedError()


class ResourceManagementActuator(Actuator):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._get_pump_targets = partial(_get_click_targets, r"pump-([a-z]+)-button")

    @attempt(route_events=[MouseButtonEvent])
    def attempt_mouse_event(self, user_action: MouseButtonEvent):
        assert isinstance(user_action, MouseButtonEvent)
        # always include the user action as it needs to be logged
        actions = [user_action]
        if user_action.status == MouseButtonEvent.CLICK and user_action.button == 0:
            actions.extend(self._get_pump_actions(user_action))
        return actions

    def _get_pump_actions(self, user_action):
        targets = self._get_pump_targets(user_action.target)
        return [TogglePumpAction(target=target) for target in targets]


class SystemMonitoringActuator(Actuator):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._get_light_targets = partial(_get_click_targets, r"light-(\d+)-button")
        self._get_slider_targets = partial(_get_click_targets, r"slider-(\d+)-button")

    @attempt(route_events=[MouseButtonEvent])
    def attempt_mouse_event(self, user_action: MouseButtonEvent):
        assert isinstance(user_action, MouseButtonEvent)
        # always include the user action as it needs to be logged
        actions = [user_action]
        if user_action.status == MouseButtonEvent.CLICK and user_action.button == 0:
            actions.extend(self._get_light_actions(user_action))
            actions.extend(self._get_slider_actions(user_action))
        return actions

    def _get_light_actions(self, user_action):
        targets = [int(x) for x in self._get_light_targets(user_action.target)]
        return [ToggleLightAction(target=target) for target in targets]

    def _get_slider_actions(self, user_action):
        targets = [int(x) for x in self._get_slider_targets(user_action.target)]
        return [ResetSliderAction(target=target) for target in targets]


def _get_click_targets(pattern, targets):
    def _get():
        for target in targets:
            match = re.match(pattern, target)
            if match:
                target = match.group(1)
                yield target

    return list(_get())
