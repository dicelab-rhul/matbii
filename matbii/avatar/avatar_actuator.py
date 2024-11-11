"""Implementation of `AvatarActuator` for the MATBII avatar.

This actuator adds functionality to quit the application via the Escape key, otherwise it has the same behaviour as `icua.agent.AvatarActuator`.
"""

from icua.agent import AvatarActuator as BaseAvatarActuator, attempt
from icua.event import UserInputEvent, KeyEvent, WindowCloseEvent
from ..utils import LOGGER


class AvatarActuator(BaseAvatarActuator):
    """AvatarActuator for the MATBII avatar."""

    @attempt
    def default(self, action: UserInputEvent):
        """Attempt method that will attempt a `UserInputEvent`, it will also convert a press to `Esc` to a `WindowCloseEvent`, triggering the environment to terminate.

        Args:
            action (UserInputEvent): user input event.
        """
        if isinstance(action, KeyEvent):
            if action.key == "escape":
                LOGGER.info("Escape was pressed, shutting down...")
                return [super().default(action), WindowCloseEvent()]
        return super().default(action)
