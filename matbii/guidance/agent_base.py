from typing import Any
from icua.event import EyeMotionEvent, MouseMotionEvent
from icua.agent import GuidanceAgent as _GuidanceAgent


class GuidanceAgent(_GuidanceAgent):
    """Base class for matbii guidance agents."""

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
