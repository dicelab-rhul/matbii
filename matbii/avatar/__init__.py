"""Package defining avatar related functionality."""

# avatar
from icua.agent import Avatar, AvatarActuator
from .exit_actuator import ExitActuator
from ..tasks import (
    AvatarTrackingActuator,
    AvatarSystemMonitoringActuator,
    AvatarResourceManagementActuator,
)

# eyetracking
from icua.extras.eyetracking import EyetrackerIOSensor, tobii

__all__ = (
    "Avatar",
    "AvatarActuator",
    "ExitActuator",
    "AvatarTrackingActuator",
    "AvatarSystemMonitoringActuator",
    "AvatarResourceManagementActuator",
    "WindowConfiguration",
    "EyetrackerIOSensor",
    "tobii",
)
