"""Package defining each of the matbii tasks.

Tasks:
    - tracking
    - system monitoring
    - resource management
"""

from .tracking import AvatarTrackingActuator, TrackingActuator, TargetMoveAction

from .resource_management import (
    ResourceManagementActuator,
    AvatarResourceManagementActuator,
    SetPumpAction,
    BurnFuelAction,
    PumpFuelAction,
    TogglePumpAction,
    TogglePumpFailureAction,
)
from .system_monitoring import (
    SystemMonitoringActuator,
    AvatarSystemMonitoringActuator,
    SetSliderAction,
    SetLightAction,
    ToggleLightAction,
    PerturbSliderAction,
    ResetSliderAction,
)


__all__ = (
    # resource managment
    "ResourceManagementActuator",
    "AvatarResourceManagementActuator",
    "SetPumpAction",
    "TogglePumpAction",
    "BurnFuelAction",
    "PumpFuelAction",
    "TogglePumpFailureAction",
    # tracking
    "AvatarTrackingActuator",
    "TrackingActuator",
    "TargetMoveAction",
    # system monitoring
    "SystemMonitoringActuator",
    "AvatarSystemMonitoringActuator",
    "SetLightAction",
    "ToggleLightAction",
    "SetSliderAction",
    "PerturbSliderAction",
    "ResetSliderAction",
)
