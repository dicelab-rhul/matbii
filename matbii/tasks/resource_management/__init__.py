"""Package that defines the matbii resource management task."""

from cerberus import rules_set_registry as _rsr
from .resource_management import (
    ResourceManagementActuator,
    AvatarResourceManagementActuator,
    SetPumpAction,
    BurnFuelAction,
    PumpFuelAction,
    TogglePumpAction,
    TogglePumpFailureAction,
)

__all__ = (
    "ResourceManagementActuator",
    "AvatarResourceManagementActuator",
    "SetPumpAction",
    "TogglePumpAction",
    "BurnFuelAction",
    "PumpFuelAction",
    "TogglePumpFailureAction",
)

# define type for pump state in configuration files, the values an be "on", "off", "failure", see SetPumpAction.coerce_pump_state
_rsr.add(
    "pump_state",
    {
        "type": "integer",
        "allowed": [0, 1, 2],
        "default": "off",
        "coerce": SetPumpAction.coerce_pump_state,
    },
)
