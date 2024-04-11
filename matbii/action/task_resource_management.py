""" Action definitions for the resource management task. """

from typing import ClassVar
from pydantic import validator
from star_ray.event import Action
from star_ray.plugin.xml import QueryXMLTemplated, QueryXML

TANK_IDS = list("abcdef")
TANK_MAIN_IDS = list("ab")
TANK_INF_IDS = list("ef")
PUMP_IDS = ["ab", "ba", "ca", "ec", "ea", "db", "fd", "fb"]


class SetPumpAction(Action):
    target: str
    state: int

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

    @validator("state", pre=True, always=True)
    @classmethod
    def _validate_state(cls, value: str | int):
        if isinstance(value, str):
            value = SetPumpAction.coerce_pump_state(value)
        if not value in (SetPumpAction.OFF, SetPumpAction.ON, SetPumpAction.FAILURE):
            raise ValueError(
                f"Invalid state `{value}` must be one of {[SetPumpAction.OFF, SetPumpAction.ON, SetPumpAction.FAILURE]}"
            )
        return value

    @staticmethod
    def coerce_pump_state(value: str | int) -> int:
        if isinstance(value, int):
            return value
        if value == "on":
            return SetPumpAction.ON
        elif value == "off":
            return SetPumpAction.OFF
        elif value == "failure":
            return SetPumpAction.FAILURE
        else:
            raise ValueError(
                f"Invalid state `{value}` must be one of ['on', 'off', 'failure']"
            )

    @staticmethod
    def new(target: int, state: int):
        return SetPumpAction(target=target, state=state)

    @staticmethod
    def new_on(target: int):
        return SetPumpAction(target=target, state=SetPumpAction.ON)

    @staticmethod
    def new_off(target: int):
        return SetPumpAction(target=target, state=SetPumpAction.OFF)

    @staticmethod
    def new_failure(target: int):
        return SetPumpAction(target=target, state=SetPumpAction.FAILURE)

    def to_xml_query(self, _) -> QueryXMLTemplated:
        return QueryXMLTemplated(
            element_id=f"pump-{self.target}-button",
            attributes={
                "data-state": "%s" % self.state,
                "fill": "{{data_colors[%s]}}" % self.state,
            },
        )


class TogglePumpAction(Action):
    target: str

    OFF: ClassVar[int] = SetPumpAction.OFF
    ON: ClassVar[int] = SetPumpAction.ON
    FAILURE: ClassVar[int] = SetPumpAction.FAILURE

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

    @staticmethod
    def new(target: int):
        return TogglePumpAction(target=target)

    def to_xml_query(self, ambient) -> QueryXMLTemplated:
        # check if pump is in a failure state
        pump_id = f"pump-{self.target}-button"
        print(pump_id)
        response = ambient.__select__(
            QueryXML(element_id=pump_id, attributes=["data-state"])
        )
        print(response)
        state = response.values["data-state"]

        if state == TogglePumpAction.FAILURE:
            return None  # toggle failed, the pump is currently in failure!

        # the pump is not in failure, toggle ON/OFF
        return QueryXMLTemplated(
            f"pump-{self.target}-button",
            {
                "data-state": "{{1-data_state}}",
                "fill": "{{data_colors[1-data_state]}}",
            },
        )


class PumpFuelAction(Action):

    target: str | int
    flow: float

    @validator("target", pre=True, always=True)
    @classmethod
    def _validate_target(cls, value):
        if isinstance(value, int):
            value = PUMP_IDS[value]
        if isinstance(value, str):
            if value in PUMP_IDS:
                return value
        raise ValueError(f"Invalid pump {value}, must be one of {PUMP_IDS}")

    def to_xml_query(self, ambient):
        id_from = self.target[0]
        id_to = self.target[1]

        _from = _get_tank_data(id_from, ambient)
        if _from["data-level"] <= 0:
            return None  # there is no fuel to transfer
        _to = _get_tank_data(id_to, ambient)
        remain = _to["data-capacity"] - _to["data-level"]
        if remain <= 0:
            return None  # the tank is full

        # compute flow value and new levels
        flow = min(_from["data-level"], remain, self.flow)
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

    target: str | int
    burn: float

    @validator("target", pre=True, always=True)
    @classmethod
    def _validate_target(cls, value):
        if isinstance(value, int):
            value = TANK_MAIN_IDS[value]
        if isinstance(value, str):
            if value in TANK_MAIN_IDS:
                return value
        raise ValueError(f"Invalid tank {value}, must be one of {TANK_MAIN_IDS}")

    def to_xml_query(self, ambient):
        values = _get_tank_data(self.target, ambient)
        if values["data-level"] == 0:
            # nothing needs to be done, there is no fuel left
            return None
        new_level = max(values["data-level"] - self.burn, 0)
        return _get_fuel_level_actions(
            self.target, new_level, values["height"], values["data-capacity"]
        )


def _get_tank_data(target, ambient):
    data = ambient.__select__(
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
