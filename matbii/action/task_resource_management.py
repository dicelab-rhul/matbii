""" Action definitions for the resource management task. """

from typing import ClassVar, List
from pydantic import validator
from star_ray.event import Action
from star_ray.plugin.xml import QueryXMLTemplated, QueryXML, QueryXPath, XMLState
from ..utils import _LOGGER

TANK_IDS = list("abcdef")
TANK_MAIN_IDS = list("ab")
TANK_INF_IDS = list("ef")
PUMP_IDS = ["ab", "ba", "ca", "ec", "ea", "db", "fd", "fb"]
ALL = "*"


class PumpAction(Action):

    target: str

    OFF: ClassVar[int] = 0
    ON: ClassVar[int] = 1
    FAILURE: ClassVar[int] = 2

    @validator("target", pre=True, always=True)
    @classmethod
    def _validate_target(cls, value: str | int):
        if isinstance(value, int):
            value = PUMP_IDS[value]
        if not value in PUMP_IDS:
            raise ValueError(
                f"{SetPumpAction.__name__} `target` {value} must be one of {PUMP_IDS}"
            )
        return value


class SetPumpAction(PumpAction):
    state: int

    @validator("state", pre=True, always=True)
    @classmethod
    def _validate_state(cls, value: str | int):
        if isinstance(value, str):
            value = SetPumpAction.coerce_pump_state(value)
        if not value in (PumpAction.OFF, PumpAction.ON, PumpAction.FAILURE):
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
    def new(target: int | str, state: int):
        return SetPumpAction(target=target, state=state)

    @staticmethod
    def new_on(target: int | str):
        return SetPumpAction(target=target, state=PumpAction.ON)

    @staticmethod
    def new_off(target: int | str):
        return SetPumpAction(target=target, state=PumpAction.OFF)

    @staticmethod
    def new_failure(target: int | str):
        return SetPumpAction(target=target, state=PumpAction.FAILURE)

    def to_xml_queries(self, _: XMLState) -> List[QueryXPath]:
        return [
            QueryXMLTemplated(
                element_id=f"pump-{self.target}-button",
                attributes={
                    "data-state": "%s" % self.state,
                    "fill": "{{data_colors[%s]}}" % self.state,
                },
            )
        ]


class TogglePumpAction(PumpAction):

    @staticmethod
    def new(target: int | str):
        return TogglePumpAction(target=target)

    def to_xml_queries(self, state: XMLState) -> List[QueryXPath]:
        # check if pump is in a failure state
        pump_id = f"pump-{self.target}-button"
        response = state.__select__(
            QueryXML(element_id=pump_id, attributes=["data-state"])
        )
        state = response.values["data-state"]
        if state == PumpAction.FAILURE:
            return []  # toggle failed, the pump is currently in failure!
        return [
            QueryXMLTemplated(
                f"pump-{self.target}-button",
                {
                    "data-state": "{{(1 - data_state)}}",
                    "fill": "{{data_colors[(1 - data_state)]}}",
                },
            )
        ]


class TogglePumpFailureAction(PumpAction):

    @staticmethod
    def new(target: int):
        return TogglePumpFailureAction(target=target)

    def to_xml_queries(self, _: XMLState) -> List[QueryXPath]:
        # update pump state: 0 or 1 -> 2, 2 -> 0
        calc = "2 * (1 - data_state // 2)"
        return [
            QueryXMLTemplated(
                f"pump-{self.target}-button",
                {
                    "data-state": "{{%s}}" % calc,
                    "fill": "{{data_colors[%s]}}" % calc,
                },
            )
        ]


class PumpFuelAction(PumpAction):

    flow: float

    # XPATH_PUMP_ALL_ON: ClassVar[str] = (
    #     "//svg:svg[@id='task_resource_management']"
    #     + "//svg:svg[contains(@id, 'pump-')]"
    #     + f"/svg:rect[@data-state='{PumpAction.ON}']"
    # )
    XPATH_PUMP_ON: ClassVar[str] = (
        "//svg:svg[@id='task_resource_management']"
        + "//svg:svg[contains(@id, 'pump-')]"
        + "/svg:rect[@id='pump-%s-button']"
    )

    def to_xml_queries(self, state: XMLState) -> List[QueryXPath]:
        if self.is_pump_on(state, self.target):
            return PumpFuelAction._get_xml_query(state, self.target, self.flow)
        return []

    def is_pump_on(self, state, target):
        xpath = PumpFuelAction.XPATH_PUMP_ON % target
        query = QueryXPath(xpath=xpath, attributes=["data-state"])
        data_state = state.__select__(query).values[0]["data-state"]
        return data_state == PumpAction.ON

    # def _get_all_on_pumps(self, state):
    #     # xpath = "//svg[@id='task_resource_management']"
    #     values = state.__select__(
    #         QueryXPath(xpath=PumpFuelAction.XPATH_PUMP_ON, attributes=["id"])
    #     ).values
    #     return [v["id"].split("-", 1)[1][:2] for v in values]

    @staticmethod
    def _get_xml_query(state, target, flow):

        id_from = target[0]
        id_to = target[1]

        _from = _get_tank_data(id_from, state)

        if _from["data-level"] <= 0:
            return []  # there is no fuel to transfer
        _to = _get_tank_data(id_to, state)

        remain = _to["data-capacity"] - _to["data-level"]
        if remain <= 0:
            return []  # the tank is full

        # compute flow value and new levels
        flow = min(_from["data-level"], remain, flow)
        new_to_level = _to["data-level"] + flow
        to_actions = _get_fuel_level_actions(
            id_to, new_to_level, _to["height"], _to["data-capacity"]
        )
        if id_from in TANK_INF_IDS:
            # "from" tank has an infinite supply, dont remove fuel
            return to_actions
        else:
            # "from" tank is a normal tank, fuel should be removed
            new_from_level = _from["data-level"] - flow
            return [
                *to_actions,
                *_get_fuel_level_actions(
                    id_from, new_from_level, _from["height"], _from["data-capacity"]
                ),
            ]


class BurnFuelAction(Action):

    target: str
    burn: float

    @validator("target", pre=True, always=True)
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

    def to_xml_queries(self, state: XMLState) -> List[QueryXPath]:
        actions = []
        if self.target != ALL:
            targets = [self.target]
        else:
            targets = TANK_MAIN_IDS
        for target in targets:
            actions.extend(
                BurnFuelAction._get_xml_burn_queries(state, target, self.burn)
            )
        return actions

    @staticmethod
    def _get_xml_burn_queries(state, target, burn):
        values = _get_tank_data(target, state)
        if values["data-level"] == 0:
            # nothing needs to be done, there is no fuel left
            return []
        new_level = max(values["data-level"] - burn, 0)
        return _get_fuel_level_actions(
            target, new_level, values["height"], values["data-capacity"]
        )


def _get_tank_data(target, state):
    data = state.__select__(
        QueryXML(
            element_id=f"tank-{target}",
            attributes=["data-level", "data-capacity", "height"],
        )
    )
    return data.values


def _get_fuel_level_actions(target, new_level, height, capacity):
    new_height = height * (new_level / capacity)
    new_y = height - new_height
    return [
        QueryXML(
            element_id=f"tank-{target}-fuel",
            attributes={"y": new_y, "height": new_height},
        ),
        QueryXML(
            element_id=f"tank-{target}",
            attributes={"data-level": new_level},
        ),
    ]
