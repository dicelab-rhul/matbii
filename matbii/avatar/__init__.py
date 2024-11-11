"""Package defining avatar related functionality."""

# avatar
from icua.agent import Avatar
from .avatar_actuator import AvatarActuator
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
    "AvatarTrackingActuator",
    "AvatarSystemMonitoringActuator",
    "AvatarResourceManagementActuator",
    "WindowConfiguration",
    "EyetrackerIOSensor",
    "tobii",
)
