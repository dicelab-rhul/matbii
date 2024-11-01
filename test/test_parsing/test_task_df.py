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


class TestTasks(unittest.TestCase):
    """Test system monitoring event parsing."""

    def test_tracking_events(self):
        """Test tracking events."""
        path = (Path(__file__).parent / "tracking.log").as_posix()
        parser, events = get_events(path)

        tracking_df = analysis.get_tracking_task_events(parser, events)
        # print(tracking_df)
        self.assertGreater(len(tracking_df), 0, "No tracking events found.")

    # def test_system_monitoring_events(self):
    #     """Test system monitoring events."""
    #     path = (Path(__file__).parent / "system_monitoring.log").as_posix()
    #     parser, events = get_events(path)

    #     system_monitoring_df = analysis.get_system_monitoring_task_events(
    #         parser, events
    #     )
    #     self.assertGreater(
    #         len(system_monitoring_df), 0, "No system monitoring events found."
    #     )


if __name__ == "__main__":
    unittest.main()
