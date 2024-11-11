"""Implementation of an actuator that will close the window when the escape key is pressed."""

from icua.agent import Actuator, attempt
from icua.event import KeyEvent, WindowCloseEvent
from ..utils import LOGGER


class ExitActuator(Actuator):
    """AvatarActuator for the MATBII avatar."""

    @attempt
    def exit(self, action: KeyEvent):
        """Attempt method for a `KeyEvent` that will convert a press to `Esc` to a `WindowCloseEvent`, triggering the environment to terminate.

        Args:
            action (KeyEvent): user input event.

        Returns:
            WindowCloseEvent: event to close the window.
        """
        if isinstance(action, KeyEvent):
            if action.key == "escape":
                LOGGER.info("Escape was pressed, shutting down...")
                return WindowCloseEvent()
