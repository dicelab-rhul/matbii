import re
from itertools import chain
from functools import partial

from star_ray.agent import ActiveActuator, attempt
from star_ray.event import MouseButtonEvent, MouseMotionEvent, KeyEvent


from ...action import ToggleLightAction, SetSliderAction, SetLightAction


class TrackingActuator(ActiveActuator):
    pass


class ResourceManagementActuator(ActiveActuator):
    pass


class SystemMonitoringActuator(ActiveActuator):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._get_light_targets = partial(
            SystemMonitoringActuator._get_click_targets, r"light-(\d+)-button"
        )
        self._get_slider_targets = partial(
            SystemMonitoringActuator._get_click_targets, r"light-(\d+)-button"
        )

    @attempt(route_events=[MouseButtonEvent])
    def attempt_mouse_event(self, user_action):
        assert isinstance(user_action, MouseButtonEvent)
        # always include the user action as it needs to be logged
        actions = [user_action]
        if user_action.status == MouseButtonEvent.CLICK and user_action.button == 0:
            actions.extend(self._get_light_actions(user_action))
            actions.extend(self._get_slider_actions(user_action))
        return actions

    def _get_light_actions(self, user_action):
        targets = self._get_light_targets(user_action.target)
        return [ToggleLightAction(target=target) for target in targets]

    def _get_slider_actions(self, user_action):
        targets = self._get_slider_targets(user_action.target)
        return [ToggleLightAction(target=target) for target in targets]

    @staticmethod
    def _get_click_targets(pattern, targets):
        def _get():
            for target in targets:
                match = re.match(pattern, target)
                if match:
                    target = int(match.group(1))
                    yield target

        return list(_get())


# class OnClickHandler:

#     def __init__(self, pattern, action_func):
#         self._pattern = pattern
#         self._action_func = action_func

#     def __call__(self, targets: List[str]):
#         for target in targets:
#             match = re.match(self._pattern, target)
#             if match:
#                 target = int(match.group(1))
#                 yield self._action_func(target=target)


# class TrackingTaskActuator(ActiveActuator):

#     def __init__(self, *args, speed=10, key_binding=None, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.keys_pressed = set()
#         self._action_map = {
#             "up": partial(TargetMoveAction.new, self.id, (0, 1)),
#             "down": partial(TargetMoveAction.new, self.id, (0, -1)),
#             "left": partial(TargetMoveAction.new, self.id, (1, 0)),
#             "right": partial(TargetMoveAction.new, self.id, (-1, 0)),
#         }
#         if key_binding is None:
#             key_binding = DEFAULT_KEY_BINDING
#         self._key_binding = key_binding
#         self._speed = speed  # this should be set based on the simulation speed...

#     @ActiveActuator.attempt
#     def attempt(self, action):
#         print(action)
#         assert isinstance(action, KeyEvent)
#         return [action]  # we always want to record the original key press/release

#     def on_key(self, action):
#         pass
