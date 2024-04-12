""" Action definitions for the system monitoring task. """

import random
from typing import List, ClassVar
from pydantic import validator, model_validator, Field

from star_ray.event import Action
from star_ray.plugin.xml import QueryXMLTemplated, QueryXPath, XMLState


# these are constants that reflect the SVG of matbii
VALID_LIGHT_IDS = [1, 2]
VALID_SLIDER_IDS = [1, 2, 3, 4]


def ToggleSliderAction(target: int) -> "SetSliderAction":
    state = random.randint(0, 1) * 2 - 1
    return SetSliderAction(target=target, state=state, relative=True)


def ResetSliderAction(target: int) -> "SetSliderAction":
    return SetSliderAction(target=target, state=None)


class SetSliderAction(Action):

    target: int  # slider to target
    state: (
        int | None
    )  # state to set, or offset from current state, or None if should reset the state.
    relative: bool = Field(
        default_factory=lambda: False
    )  # is `state` relative to the current state?

    @validator("target", pre=True, always=True)
    @classmethod
    def _validate_target(cls, value):
        if not value in VALID_SLIDER_IDS:
            raise ValueError(f"`target` {value} must be one of {VALID_LIGHT_IDS}")
        return value

    @model_validator(mode="after")
    @classmethod
    def _validate(cls, obj):
        if obj.state is None:
            obj.relative = False
        return obj

    def to_xml_queries(self, state: XMLState) -> List[QueryXPath]:
        # get min and max values for the number of increments
        inc_target = f"slider-{self.target}-incs"
        but_target = f"slider-{self.target}-button"
        query = QueryXPath(
            xpath=f"//*[@id='{inc_target}']/svg:line", attributes=["y1", "data-state"]
        )
        response = state.__select__(query)
        states = {x["data-state"]: x["y1"] for x in response.values}
        inc_size = states[2] - states[1]  # TODO check that these are all the same?

        min_state, max_state = (min(states.keys()), max(states.keys()))
        # -1 here because of the size of the slider button
        # TODO this should really be computed based on the button size relative to inc_size?
        max_state = max_state - 1
        state = self.state

        if state is None:
            state = max_state // 2 + 1

        # we select the parent of the button node because it contains the state and position to update
        xpath_parent = f"//*[@id='{but_target}']/parent::node()"
        if self.relative:
            query = QueryXPath(
                xpath=xpath_parent,
                attributes=["data-state"],
            )
            response = state.__select__(query)
            state = response.values[0]["data-state"] + self.state

        # new state should not overflow
        state = min(max(min_state, state), max_state)
        new_y = states[state] - inc_size

        # query the state to get the required properties
        return [
            QueryXPath(
                xpath=xpath_parent,
                attributes={"data-state": state, "y": new_y},
            )
        ]


class SetLightAction(Action):
    target: int
    state: int

    OFF: ClassVar[int] = 0
    ON: ClassVar[int] = 1

    @validator("target", pre=True, always=True)
    @classmethod
    def _validate_target(cls, value):
        if not value in VALID_LIGHT_IDS:
            raise ValueError(f"`target` {value} must be one of {VALID_LIGHT_IDS}")
        return value

    @validator("state", pre=True, always=True)
    @classmethod
    def _validate_state(cls, value: int | str):
        if isinstance(value, str):
            value = SetLightAction.coerce_light_state(value)
        if not value in (SetLightAction.OFF, SetLightAction.ON):
            raise ValueError(
                f"Invalid state `{value}` must be one of {[SetLightAction.OFF, SetLightAction.ON]}"
            )
        return value

    @staticmethod
    def coerce_light_state(value: str | int):
        if isinstance(value, int):
            return value
        if value == "on":
            return SetLightAction.ON
        elif value == "off":
            return SetLightAction.OFF
        else:
            raise ValueError(f"Invalid state `{value}` must be one of ['on', 'off']")

    @staticmethod
    def new(target: int, state: int):
        return SetLightAction(target=target, state=state)

    @staticmethod
    def new_unacceptable(target: int):
        # TODO assumes failure state = 1
        return SetLightAction(target=target, state=1)

    @staticmethod
    def new_acceptable(target: int):
        # TODO assumes failure state = 0
        return SetLightAction(target=target, state=0)

    def to_xml_queries(self, state: XMLState) -> List[QueryXPath]:
        return [
            QueryXMLTemplated(
                element_id=f"light-{self.target}-button",
                attributes={
                    "data-state": "%s" % self.state,
                    "fill": "{{data_colors[%s]}}" % self.state,
                },
            )
        ]


class ToggleLightAction(Action):
    target: int

    @validator("target", pre=True, always=True)
    @classmethod
    def _validate_target(cls, value):
        if not value in VALID_LIGHT_IDS:
            raise ValueError(f"`target` {value} must be one of {VALID_LIGHT_IDS}")
        return value

    @staticmethod
    def new(target: int):
        return SetLightAction(target=target)

    def to_xml_queries(self, state: XMLState) -> List[QueryXPath]:
        return [
            QueryXMLTemplated(
                f"light-{self.target}-button",
                {
                    "data-state": "{{1-data_state}}",
                    "fill": "{{data_colors[1-data_state]}}",
                },
            )
        ]
