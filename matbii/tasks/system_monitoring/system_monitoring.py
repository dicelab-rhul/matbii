"""Module that implements the "system monitoring" task.

This files contains:
    - avatar actuator: `AvatarSystemMonitoringActuator`
    - agent actuator: `SystemMonitoringActuator`
    - actions: [`TargetMoveAction`, `PerturbSliderAction`, `ResetSliderAction`, `SetSliderAction`, `SetLightAction`, `ToggleLightAction`]
"""

import random
import re
from typing import Any, ClassVar, Union
from functools import partial
from pydantic import Field, field_validator


from icua.agent import agent_actuator, attempt, Actuator
from icua.event import XMLUpdateQuery, MouseButtonEvent

from star_ray_xml import (
    XMLState,
    Expr,
    update,
    select,
)

# these are constants that reflect the task svg TODO move to _const?
VALID_LIGHT_IDS = [1, 2]
VALID_SLIDER_IDS = [1, 2, 3, 4]


__all__ = (
    "AvatarSystemMonitoringActuator",
    "SystemMonitoringActuator",
    "PerturbSliderAction",
    "ResetSliderAction",
    "SetSliderAction",
    "SetLightAction",
    "ToggleLightAction",
)


class AvatarSystemMonitoringActuator(Actuator):
    """Actuator class that should be added to the Avatar when the system monitoring task is enabled. It allows the user to control the lights and sliders in this task."""

    def __init__(self, *args: list[Any], **kwargs: dict[str, Any]):
        """Constructor.

        Args:
            args (list[Any], optional): additional optional arguments.
            kwargs (dict[Any], optional): additional optional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self._get_light_targets = partial(
            AvatarSystemMonitoringActuator.get_click_targets, r"light-(\d+)-button"
        )
        self._get_slider_targets = partial(
            AvatarSystemMonitoringActuator.get_click_targets, r"slider-(\d+)-button"
        )

    @attempt
    def attempt_mouse_event(
        self, user_action: MouseButtonEvent
    ) -> list[Union["SetLightAction", "SetSliderAction"]]:
        """Attempt method that takes a `MouseButtonEvent` as input from the user. It is up to the avatar to provide this event to this actuator. The information is essential if the user is to control this task.

        This will attempt either a `SetLightAction` or a `SetSliderAction` depending on what svg element was clicked (assuming the mouse event registers as a click).

        Effects:
        - `SetLightAction`: will always set the light to its preferred (acceptable) state (which is ON for light 1 and OFF for light 2).
        - `SetSliderAction` will reset the slider to its preferred (acceptable) state (which is the central position), see `ResetSliderAction`.

        Args:
            user_action (MouseButtonEvent): the users mouse button action.

        Returns:
            list[SetLightAction | SetSliderAction]: the action to be attempted
        """
        assert isinstance(user_action, MouseButtonEvent)
        actions = []
        if (
            user_action.status == MouseButtonEvent.DOWN
            and user_action.button == MouseButtonEvent.BUTTON_LEFT
        ):
            actions.extend(self._get_light_actions(user_action))
            actions.extend(self._get_slider_actions(user_action))
        return actions

    def _get_light_actions(
        self, user_action: MouseButtonEvent
    ) -> list["ToggleLightAction"]:
        targets = [int(x) for x in self._get_light_targets(user_action.target)]
        # the user can only set the state to the "acceptable" state
        acceptable = [
            SetLightAction.ON,
            SetLightAction.OFF,
        ]
        return [
            SetLightAction(target=target, state=acceptable[target - 1])
            for target in targets
        ]

    def _get_slider_actions(
        self, user_action: MouseButtonEvent
    ) -> list["SetSliderAction"]:
        targets = [int(x) for x in self._get_slider_targets(user_action.target)]
        return [ResetSliderAction(target=target) for target in targets]

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


@agent_actuator
class SystemMonitoringActuator(Actuator):
    """Actuator class that will be part of a `ScheduledAgent` or any other agent that controls the evolution of the system monitoring task."""

    @attempt
    def on_light(self, target: int) -> "SetLightAction":
        """Switch the `target` light to the "on" state.

        Args:
            target (int): the integer `id` of the target light (1 or 2).

        Returns:
            SetLightAction: the action
        """
        return SetLightAction(target=target, state=SetLightAction.ON)

    @attempt
    def off_light(self, target: int) -> "SetLightAction":
        """Switch the `target` light to the "off" state.

        Args:
            target (int): the integer `id` of the target light (1 or 2).

        Returns:
            SetLightAction: the action
        """
        return SetLightAction(target=target, state=SetLightAction.OFF)

    @attempt
    def toggle_light(self, target: int) -> "SetLightAction":
        """Toggle the `target` light (on->off, off->on).

        Args:
            target (int): the integer `id` of the target light (1 or 2).

        Returns:
            SetLightAction: the action
        """
        return ToggleLightAction(target=target)

    @attempt
    def perturb_slider(self, target: int) -> "SetSliderAction":
        """Perturb the `target` slider by +/- 1 slot.

        Args:
            target (int): the integer `id` of the target slider (1, 2, 3 or 4).

        Returns:
            SetSliderAction: the action
        """
        state = 2 * random.randint(0, 1) - 1  # randomly perturb +/- 1
        return SetSliderAction(target=target, state=state, relative=True)


def PerturbSliderAction(target: int) -> "SetSliderAction":
    """Perturb the `target` slider by +/- 1 slot.

    Args:
        target (int): the integer `id` of the target slider (1, 2, 3 or 4).

    Returns:
        SetSliderAction: the action
    """
    state = random.randint(0, 1) * 2 - 1
    return SetSliderAction(target=target, state=state, relative=True)


def ResetSliderAction(target: int) -> "SetSliderAction":
    """Reset the `target` slider to its central position.

    Args:
        target (int): the integer `id` of the target slider (1, 2, 3 or 4).

    Returns:
        SetSliderAction: the action
    """
    return SetSliderAction(target=target, state=None, relative=False)


class SetSliderAction(XMLUpdateQuery):
    """Action class that will update a sliders's state. The state of a slider is the integer index of one of its increments."""

    # slider to target
    target: int
    # state to set, or offset from current state, or None if should reset the state.
    state: int | None
    # is `state` relative to the current state?
    relative: bool = Field(default_factory=lambda: False)

    @field_validator("target", mode="before")
    @classmethod
    def _validate_target(cls, value):
        if value not in VALID_SLIDER_IDS:
            raise ValueError(f"`target` {value} must be one of {VALID_LIGHT_IDS}")
        return value

    @staticmethod
    def acceptable_state(increments: int) -> int:
        """Defines the acceptable state of the slider. This is the state that the slider will return to if the actions `state` field is None.

        Args:
            increments (int): the number of increments in the slider.

        Returns:
            int: the acceptable state of the slider
        """
        return increments // 2

    def __execute__(self, xml_state: XMLState) -> Any:  # noqa
        # get min and max values for the number of increments
        inc_target = f"slider-{self.target}-incs"
        but_target = f"slider-{self.target}-button"
        response = xml_state.select(
            select(
                xpath=f"//*[@id='{inc_target}']/svg:line",
                attrs=["y1", "data-state"],
            )
        )
        states = {x["data-state"]: x["y1"] for x in response}
        # TODO check that these are all the same?
        inc_size = states[2] - states[1]
        min_state, max_state = (min(states.keys()), max(states.keys()) - 1)
        state = self.state
        if state is None:
            self.relative = False
            state = SetSliderAction.acceptable_state(max_state + 1)

        # we select the parent of the button node because it contains the state and position to update
        xpath_parent = f"//*[@id='{but_target}']/parent::node()"
        if self.relative:
            # update the state relative to the current state
            response = xml_state.select(
                select(
                    xpath=xpath_parent,
                    attrs=["data-state"],
                )
            )
            assert len(response) == 1
            state = response[0]["data-state"] + self.state

        # new state should not overflow
        state = min(max(min_state, state), max_state)
        new_y = states[state] - inc_size
        return xml_state.update(
            update(
                xpath=xpath_parent,
                attrs={"data-state": state, "y": new_y},
            )
        )


class SetLightAction(XMLUpdateQuery):
    """Action class that will update a light's state (on=1 or off=0)."""

    target: int  # the target light
    state: int  # the new state of the light

    OFF: ClassVar[int] = 0  # off state
    ON: ClassVar[int] = 1  # on state

    @field_validator("target", mode="before")
    @classmethod
    def _validate_target(cls, value):
        if value not in VALID_LIGHT_IDS:
            raise ValueError(f"`target` {value} must be one of {VALID_LIGHT_IDS}")
        return value

    @field_validator("state", mode="before")
    @classmethod
    def _validate_state(cls, value: int | str):
        if isinstance(value, str):
            value = SetLightAction.coerce_light_state(value)
        if value not in (SetLightAction.OFF, SetLightAction.ON):
            raise ValueError(
                f"Invalid state `{value}` must be one of {[SetLightAction.OFF, SetLightAction.ON]}"
            )
        return value

    @staticmethod
    def coerce_light_state(value: str | int) -> int:
        """Coerce a state that is specified as a string to an int: "off -> 0, "on" -> 1.

        Args:
            value (str | int): the value to coerce valid values: 0,1,"on","off.

        Raises:
            ValueError: if the given state cannot be  coerced.

        Returns:
            int: the integer state.
        """
        if isinstance(value, int):
            return value
        if value == "on":
            return SetLightAction.ON
        elif value == "off":
            return SetLightAction.OFF
        else:
            raise ValueError(f"Invalid state `{value}` must be one of ['on', 'off']")

    def __execute__(self, xml_state: XMLState):  # noqa
        xml_state.update(
            update(
                xpath=f"//*[@id='light-{self.target}-button']",
                attrs={
                    "data-state": str(self.state),
                    "fill": Expr("{data-colors}[{state}]", state=self.state),
                },
            )
        )


class ToggleLightAction(XMLUpdateQuery):
    """Action class that will toggle a light's state from on->off and off->on."""

    target: int

    @field_validator("target", mode="before")
    @classmethod
    def _validate_target(cls, value):
        if value not in VALID_LIGHT_IDS:
            raise ValueError(f"`target` {value} must be one of {VALID_LIGHT_IDS}")
        return value

    def __execute__(self, xml_state: XMLState):  # noqa
        xml_state.update(
            update(
                xpath=f"//*[@id='light-{self.target}-button']",
                attrs={
                    "data-state": Expr("1-{data-state}"),
                    # GOTCHA! data-state will be updated first (above) and used to update fill! the dict order matters here.
                    "fill": Expr("{data-colors}[{data-state}]"),
                },
            )
        )
