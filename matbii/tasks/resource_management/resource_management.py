"""Module that implements the [resource management task][matbii.tasks.resource_management].

This files contains:
    - avatar actuator: `AvatarResourceManagementActuator`
    - agent actuator: `ResourceManagementActuator`
    - actions: [`SetPumpAction`, `TogglePumpAction`, `TogglePumpFailureAction`, `PumpFuelAction`, `BurnFuelAction`]
"""

import re
from typing import ClassVar, Literal, Any
from pydantic import field_validator
from functools import partial
from star_ray_xml import update, select, XMLState, Expr
from star_ray_xml.query import XMLUpdateQuery

from icua.event import MouseButtonEvent
from icua.agent import attempt, Actuator

TANK_IDS = list("abcdef")
TANK_MAIN_IDS = list("ab")
TANK_INF_IDS = list("ef")
PUMP_IDS = ["ab", "ba", "ca", "ec", "ea", "db", "fd", "fb"]
ALL = "*"

__all__ = (
    "ResourceManagementActuator",
    "AvatarResourceManagementActuator",
    "SetPumpAction",
    "TogglePumpAction",
    "BurnFuelAction",
    "PumpFuelAction",
    "TogglePumpFailureAction",
)


class AvatarResourceManagementActuator(Actuator):
    """Actuator class that should be added to the Avatar when the resource management task is enabled. It allows the user to control the pumps in this task.."""

    def __init__(self, *args: list[Any], **kwargs: dict[str, Any]):
        """Constructor.

        Args:
            args (list[Any], optional): additional optional arguments.
            kwargs (dict[Any], optional): additional optional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self._get_pump_targets = partial(
            AvatarResourceManagementActuator.get_click_targets, r"pump-([a-z]+)-button"
        )

    @attempt
    def attempt_mouse_event(
        self, user_action: MouseButtonEvent
    ) -> list["TogglePumpAction"]:
        """Attempt method that takes a `MouseButtonEvent` as input from the user. It is up to the avatar to provide this event to this actuator. The information is essential if the user is to control this task.

        This will attempt a `TogglePumpAction` depending on what svg element was clicked (assuming the mouse event registers as a click).

        Effects:
        - `TogglePumpAction`: toggle the pump on->off or off->on.

        Args:
            user_action (MouseButtonEvent): the users mouse button action.

        Returns:
            list[TogglePumpAction]: the action to be attempted
        """
        assert isinstance(user_action, MouseButtonEvent)
        # always include the user action as it needs to be logged
        actions = []
        if (
            user_action.status == MouseButtonEvent.DOWN
            and user_action.button == MouseButtonEvent.BUTTON_LEFT
        ):
            actions.extend(self._get_pump_actions(user_action))
        return actions

    def _get_pump_actions(
        self, user_action: MouseButtonEvent
    ) -> list["TogglePumpAction"]:
        targets = self._get_pump_targets(user_action.target)
        return [TogglePumpAction(target=target) for target in targets]

    @staticmethod
    def get_click_targets(pattern: str, targets: list[str]) -> list[str]:
        """Extras the `id` field of a target in `targets` if it matches the pattern.

        Args:
            pattern (str): pattern to test.
            targets (list[str]): targets to search.

        Returns:
            list[str]: matching targets.
        """

        def _get():
            for target in targets:
                match = re.match(pattern, target)
                if match:
                    target = match.group(1)
                    yield target

        return list(_get())


class ResourceManagementActuator(Actuator):
    """Actuator class that will be part of a `ScheduledAgent` or any other agent that controls the evolution of the resource management task."""

    @attempt
    def burn_fuel(
        self,
        target: int | str,
        burn: float,
    ) -> "BurnFuelAction":
        """Burns a given amount of fuel in the `target` tank, if the tank is empty this has no effect.

        Args:
            target (int | Literal["a", "b"]): target tank
            burn (float): amount of fuel to burn.

        Returns:
            BurnFuelAction: the action
        """
        return BurnFuelAction(target=target, burn=burn)

    @attempt
    def pump_fuel(
        self,
        target: int | str,
        flow: float,
    ) -> "PumpFuelAction":
        """Pumps the given amount of fuel via the given pump.

        Args:
            target (int | Literal["ab", "ba", "ca", "ec", "ea", "db", "fd", "fb"]): target pump (this will determine which tanks are pumped to/from).
            flow (float): amount of fuel to pump.

        Returns:
            PumpFuelAction: the action
        """
        return PumpFuelAction(target=target, flow=flow)

    @attempt
    def toggle_pump_failure(
        self,
        target: int | str,
    ) -> "TogglePumpFailureAction":
        """Toggle a pump failure (on/off -> failure, failure -> off).

        Args:
            target (int | Literal["ab", "ba", "ca", "ec", "ea", "db", "fd", "fb"]): target pump.

        Returns:
            TogglePumpFailureAction: the action
        """
        return TogglePumpFailureAction(target=target)

    @attempt
    def toggle_pump(
        self,
        target: int | str,
    ) -> "TogglePumpAction":
        """Toggle pump state (on -> off, off -> on).

        Args:
            target (int | Literal["ab", "ba", "ca", "ec", "ea", "db", "fd", "fb"]): target pump.

        Returns:
            TogglePumpFailureAction: the action
        """
        return TogglePumpAction(target=target)


class PumpAction(XMLUpdateQuery):
    """Base class for pump related actions."""

    target: str

    OFF: ClassVar[int] = 0
    ON: ClassVar[int] = 1
    FAILURE: ClassVar[int] = 2

    @field_validator("target", mode="before")
    @classmethod
    def _validate_target(cls, value: str | int):
        if isinstance(value, int):
            value = PUMP_IDS[value]
        if value not in PUMP_IDS:
            raise ValueError(
                f"{SetPumpAction.__name__} `target` {value} must be one of {PUMP_IDS}"
            )
        return value


class SetPumpAction(PumpAction):
    """Action class for setting the state of a pump. Pumps states are off=0, on=1, failure=2."""

    state: int

    @field_validator("state", mode="before")
    @classmethod
    def _validate_state(cls, value: str | int):
        if isinstance(value, str):
            value = SetPumpAction.coerce_pump_state(value)
        if value not in (PumpAction.OFF, PumpAction.ON, PumpAction.FAILURE):
            raise ValueError(
                f"Invalid state `{value}` must be one of {[PumpAction.OFF, PumpAction.ON, PumpAction.FAILURE]}"
            )
        return value

    @staticmethod
    def coerce_pump_state(value: int | str) -> int:
        """Coerce a state that is specified as a string to an int: "off -> 0, "on" -> 1, "failure" -> 2.

        Args:
            value (str | int): the value to coerce.

        Raises:
            ValueError: if the given state cannot be coerced.

        Returns:
            int: the integer state.
        """
        if isinstance(value, int):
            return value
        if value == "on":
            return PumpAction.ON
        elif value == "off":
            return PumpAction.OFF
        elif value == "failure":
            return PumpAction.FAILURE
        else:
            raise ValueError(
                f"Invalid state `{value}` must be one of ['on', 'off', 'failure']"
            )

    @staticmethod
    def new_on(target: int | str) -> "SetPumpAction":
        """Factory method that returns an action that will turn the given pump on.

        Args:
            target (int | str): target pump.

        Returns:
            SetPumpAction: the action
        """
        return SetPumpAction(target=target, state=PumpAction.ON)

    @staticmethod
    def new_off(target: int | str) -> "SetPumpAction":
        """Factory method that returns an action that will turn the given pump off.

        Args:
            target (int | str): target pump.

        Returns:
            SetPumpAction: the action
        """
        return SetPumpAction(target=target, state=PumpAction.OFF)

    @staticmethod
    def new_failure(target: int | str) -> "SetPumpAction":
        """Factory function that returns an action that will make the pump fail.

        Args:
            target (int | str): target pump.

        Returns:
            SetPumpAction: the action
        """
        return SetPumpAction(target=target, state=PumpAction.FAILURE)

    def __execute__(self, state: XMLState):  # noqa
        return state.update(
            update(
                xpath=f"//*[@id='pump-{self.target}-button']",
                attrs={
                    "data-state": str(self.state),
                    "fill": Expr("{data-colors}[{state}]", state=self.state),
                },
            )
        )


class TogglePumpAction(PumpAction):
    """Action class that will toggle the pump on -> off, off -> on."""

    @staticmethod
    def new(
        target: int | Literal["ab", "ba", "ca", "ec", "ea", "db", "fd", "fb"],
    ) -> "TogglePumpAction":
        """Factory function for a `TogglePumpAction`.

        Args:
            target (int | Literal["ab", "ba", "ca", "ec", "ea", "db", "fd", "fb"]): target pump

        Returns:
            TogglePumpAction: the action.
        """
        return TogglePumpAction(target=target)

    def __execute__(self, xml_state: XMLState):  # noqa
        # check if pump is in a failure state
        pump_id = f"pump-{self.target}-button"
        # 0 -> 1, 1 -> 0, 2 -> 2 (cannot toggle if the pump is in failure)
        new_state = "(1-{data-state})%3"
        xml_state.update(
            update(
                xpath=f"//*[@id='{pump_id}']",
                attrs={
                    "data-state": Expr(new_state),
                    # GOTCHA! data-state will be updated first (from above) and used to update fill! the order matters here.
                    "fill": Expr("{data-colors}[{data-state}]"),
                },
            )
        )


class TogglePumpFailureAction(PumpAction):
    """Action class that will cause a pump failure (on/off -> failure, failure -> off)."""

    @staticmethod
    def new(target: int) -> "TogglePumpFailureAction":
        """Factory function for a `TogglePumpFailureAction`.

        Args:
            target (int | Literal["ab", "ba", "ca", "ec", "ea", "db", "fd", "fb"]): target pump

        Returns:
            TogglePumpFailureAction: the action.
        """
        return TogglePumpFailureAction(target=target)

    def __execute__(self, xml_state: XMLState):  # noqa
        pump_id = f"pump-{self.target}-button"
        # 0 -> 2, 1 -> 2, 2 -> 0
        new_state = "2 * (1 - {data-state} // 2)"
        xml_state.update(
            update(
                xpath=f"//*[@id='{pump_id}']",
                attrs={
                    "data-state": Expr(new_state),
                    # GOTCHA! data-state will be updated first (from above) and used to update fill! the order matters here.
                    "fill": Expr("{data-colors}[{data-state}]"),
                },
            )
        )


class PumpFuelAction(PumpAction):
    """Action class that will pump fuel from one tank to another."""

    flow: float
    XPATH_PUMP: ClassVar[str] = "//svg:rect[@id='pump-%s-button']"

    def __execute__(self, xml_state: XMLState):  # noqa
        if self.is_pump_on(xml_state, self.target):
            id_from = self.target[0]
            id_to = self.target[1]

            _from = _get_tank_data(xml_state, id_from)
            if _from["data-level"] <= 0:
                return  # there is no fuel to transfer
            _to = _get_tank_data(xml_state, id_to)
            remain = _to["data-capacity"] - _to["data-level"]
            if remain <= 0:
                return  # the tank is full

            # compute flow value and new levels
            # TODO potential weird bug here if _from["data-level"] is lower than flow for an infinite tank
            flow = min(_from["data-level"], remain, self.flow)
            new_to_level = _to["data-level"] + flow
            _update_tank_level(xml_state, id_to, _to, new_to_level)
            if id_from not in TANK_INF_IDS:
                # "from" tank is a normal tank, fuel should be removed
                new_from_level = _from["data-level"] - flow
                _update_tank_level(xml_state, id_from, _from, new_from_level)

    def is_pump_on(self, xml_state: XMLState, target: str) -> bool:
        """Is the given pump current in the "on" state?

        Args:
            xml_state (XMLState): environment state.
            target (str): target pump.

        Returns:
            bool: whether the pump is on.
        """
        xpath = PumpFuelAction.XPATH_PUMP % target
        data_state = xml_state.select(select(xpath=xpath, attrs=["data-state"]))[0][
            "data-state"
        ]
        return data_state == PumpAction.ON


class BurnFuelAction(XMLUpdateQuery):
    """Action class that will burn fuel in one of the main tanks (tank id = "a", "b" or "*" which indicates both tanks)."""

    target: str
    burn: float

    @field_validator("target", mode="before")
    @classmethod
    def _validate_target(cls, value: int | str) -> str:
        if isinstance(value, int):
            value = TANK_MAIN_IDS[value]
        if isinstance(value, str):
            if value in TANK_MAIN_IDS + [ALL]:
                return value
        raise ValueError(
            f"Invalid tank {value}, must be one of {TANK_MAIN_IDS + [ALL]}"
        )

    def __execute__(self, xml_state: XMLState):  # noqa
        targets = self._get_targets()
        for target in targets:
            values = _get_tank_data(xml_state, target)
            if values["data-level"] == 0:
                continue  # fuel is already 0, no fuel to burn
            new_level = max(values["data-level"] - self.burn, 0)
            _update_tank_level(xml_state, target, values, new_level)

    def _get_targets(self) -> list[str]:
        if self.target != ALL:
            targets = [self.target]
        else:
            targets = TANK_MAIN_IDS
        return targets


def _update_tank_level(
    xml_state: XMLState, tank: str, tank_data: dict[str, Any], new_level: float
):
    # updates the level of a tank
    new_height = tank_data["height"] * (new_level / tank_data["data-capacity"])
    new_y = tank_data["height"] - new_height
    xml_state.update(
        update(
            xpath=f"//*[@id='tank-{tank}-fuel']",
            attrs={"y": new_y, "height": new_height},
        )
    )
    xml_state.update(
        update(
            xpath=f"//*[@id='tank-{tank}']",
            attrs={"data-level": new_level},
        )
    )


def _get_tank_data(xml_state: XMLState, tank: str) -> dict[str, Any]:
    # getter for tank data
    return xml_state.select(
        select(
            xpath=f"//*[@id='tank-{tank}']",
            attrs=["data-level", "data-capacity", "height"],
        )
    )[0]
