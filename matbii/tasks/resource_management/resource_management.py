import re
from typing import ClassVar
from pydantic import field_validator
from functools import partial
from star_ray_xml import update, select, XMLState, Expr
from star_ray_xml.query import XMLUpdateQuery

from icua.event import MouseButtonEvent
from icua.agent import attempt, Actuator
import time

TANK_IDS = list("abcdef")
TANK_MAIN_IDS = list("ab")
TANK_INF_IDS = list("ef")
PUMP_IDS = ["ab", "ba", "ca", "ec", "ea", "db", "fd", "fb"]
ALL = "*"


class AvatarResourceManagementActuator(Actuator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._get_pump_targets = partial(
            AvatarResourceManagementActuator.get_click_targets, r"pump-([a-z]+)-button"
        )

    @attempt
    def attempt_mouse_event(self, user_action: MouseButtonEvent):
        assert isinstance(user_action, MouseButtonEvent)
        # always include the user action as it needs to be logged
        actions = []
        if (
            user_action.status == MouseButtonEvent.DOWN
            and user_action.button == MouseButtonEvent.BUTTON_LEFT
        ):
            actions.extend(self._get_pump_actions(user_action))
        return actions

    def _get_pump_actions(self, user_action):
        targets = self._get_pump_targets(user_action.target)
        return [TogglePumpAction(target=target) for target in targets]

    @staticmethod
    def get_click_targets(pattern, targets):
        def _get():
            for target in targets:
                match = re.match(pattern, target)
                if match:
                    target = match.group(1)
                    yield target

        return list(_get())


class ResourceManagementActuator(Actuator):
    @attempt
    def burn_fuel(self, target: int | str, burn: float):
        #print("burn", target, time.time())
        """Burns a given amount of fuel in the target tank."""
        return BurnFuelAction(target=target, burn=burn)

    @attempt
    def pump_fuel(self, target: int | str, flow: float):
        #print("?????", target, time.time())
        """Pumps a given amount of fuel to/from the given tanks."""
        return PumpFuelAction(target=target, flow=flow)

    @attempt
    def toggle_pump_failure(self, target: int | str):
        """Toggle a pump failure (on/off -> failure, failure -> off)"""
        return TogglePumpFailureAction(target=target)

    @attempt
    def toggle_pump(self, target: int | str):
        """Toggle pump state (on->off, off->on)"""
        return TogglePumpAction(target=target)


class PumpAction(XMLUpdateQuery):
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
    def new_on(target: int | str):
        return SetPumpAction(target=target, state=PumpAction.ON)

    @staticmethod
    def new_off(target: int | str):
        return SetPumpAction(target=target, state=PumpAction.OFF)

    @staticmethod
    def new_failure(target: int | str):
        return SetPumpAction(target=target, state=PumpAction.FAILURE)

    def __execute__(self, state: XMLState):
        return state.update(
            update(
                xpath=f"//*[@id='pump-{self.target}-button']",
                attrs={
                    "data-state": "%s" % self.state,
                    "fill": Expr("{data-colors}[{state}]", state=self.state),
                },
            )
        )


class TogglePumpAction(PumpAction):
    @staticmethod
    def new(target: int | str):
        return TogglePumpAction(target=target)

    def __execute__(self, xml_state: XMLState):
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
    @staticmethod
    def new(target: int):
        return TogglePumpFailureAction(target=target)

    def __execute__(self, xml_state: XMLState):
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
    flow: float
    XPATH_PUMP: ClassVar[str] = "//svg:rect[@id='pump-%s-button']"

    def __execute__(self, xml_state: XMLState):
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

    def is_pump_on(self, xml_state: XMLState, target: str):
        xpath = PumpFuelAction.XPATH_PUMP % target
        data_state = xml_state.select(select(xpath=xpath, attrs=["data-state"]))[0][
            "data-state"
        ]
        return data_state == PumpAction.ON


class BurnFuelAction(XMLUpdateQuery):
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

    def __execute__(self, xml_state: XMLState):
        #print("---", time.time())
        targets = self.get_targets()
        for target in targets:
            values = _get_tank_data(xml_state, target)
            if values["data-level"] == 0:
                continue  # fuel is already 0, no fuel to burn
            new_level = max(values["data-level"] - self.burn, 0)
            _update_tank_level(xml_state, target, values, new_level)

    def get_targets(self):
        if self.target != ALL:
            targets = [self.target]
        else:
            targets = TANK_MAIN_IDS
        return targets


def _update_tank_level(xml_state, tank, tank_data, new_level):
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


def _get_tank_data(xml_state, tank):
    return xml_state.select(
        select(
            xpath=f"//*[@id='tank-{tank}']",
            attrs=["data-level", "data-capacity", "height"],
        )
    )[0]
