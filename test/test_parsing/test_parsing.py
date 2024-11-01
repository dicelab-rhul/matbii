"""Test mouse and keyboard event parsing."""

import unittest
import matbii.extras.analysis as analysis
from pathlib import Path


def get_events(path: str | Path):
    """Get events from a log file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Test log file not found: {path.as_posix()}")
    parser = analysis.EventLogParser()
    parser.discover_event_classes("matbii")
    return parser, list(parser.parse(path, relative_start=True))


class TestSystemMonitoringEvents(unittest.TestCase):
    """Test system monitoring event parsing."""

    @classmethod
    def setUpClass(cls):
        """Get events from the system monitoring test log file."""
        path = (Path(__file__).parent / "system_monitoring.log").as_posix()
        cls.parser, cls.events = get_events(path)

    def test_system_monitoring_events(self):
        """Test system monitoring events."""
        system_monitoring_df = analysis.get_system_monitoring_task_events(
            self.parser, self.events
        )
        self.assertGreater(
            len(system_monitoring_df), 0, "No system monitoring events found."
        )


class TestUserInputEvents(unittest.TestCase):
    """Test mouse, keyboard and eyetracking event parsing."""

    @classmethod
    def setUpClass(cls):
        """Get events from the user input test log file."""
        path = (Path(__file__).parent / "user_input.log").as_posix()
        cls.parser, cls.events = get_events(path)

    def test_eyetracking_events(self):  # noqa
        eyetracking_df = analysis.get_eyetracking_events(self.parser, self.events)
        self.assertGreater(len(eyetracking_df), 0, "No eyetracking events found.")

    def test_mouse_button_events(self):  # noqa
        mouse_button_df = analysis.get_mouse_button_events(self.parser, self.events)
        self.assertGreater(len(mouse_button_df), 0, "No mouse button events found.")

    def test_mouse_motion_events(self):  # noqa
        mouse_motion_df = analysis.get_mouse_motion_events(self.parser, self.events)
        self.assertGreater(len(mouse_motion_df), 0, "No mouse motion events found.")

    def test_keyboard_events(self):  # noqa
        keyboard_df = analysis.get_keyboard_events(self.parser, self.events)
        self.assertGreater(len(keyboard_df), 0, "No keyboard events found.")


if __name__ == "__main__":
    unittest.main()
