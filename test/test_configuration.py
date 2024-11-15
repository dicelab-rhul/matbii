"""Tests for the class: `matbii.config.Configuration`."""

from matbii.config import Configuration
from matbii.utils import get_class_from_fqn
from matbii.guidance import ArrowGuidanceActuator


def test_configuration():
    """Tests that the validators in `Configuration` are working correctly on default data."""
    Configuration()


def test_get_class_from_fqn():
    """Tests the utility function `get_class_from_fqn`."""
    fqn = "matbii.guidance.ArrowGuidanceActuator"
    cls = get_class_from_fqn(fqn)
    if cls != ArrowGuidanceActuator:
        raise ValueError(f"Failed to find class by fully qualified name: {fqn}.")
