"""Eyetracking visualisation. This will create an avatar that displays the mouse and gaze location of the user. It may be used for debugging purposes, or to choose suitable parameters for a new eyetracker."""

from icua import MultiTaskEnvironment
from icua.agent import Avatar as _Avatar, Actuator as _Actuator, attempt, observe
from icua.event import MouseMotionEvent, EyeMotionEvent, WindowCloseEvent
from star_ray_xml import Update
from matbii.config import EyetrackingConfiguration, WindowConfiguration
import argparse

from star_ray.utils import _LOGGER

# silence logs from star_ray logger
_LOGGER.setLevel("WARNING")

argparser = argparse.ArgumentParser()
argparser.add_argument("--uri", type=str)
argparser.add_argument("--sdk", type=str, default="tobii")

args = argparser.parse_args()

window_config = WindowConfiguration(
    width=640,
    height=640,
    title="Eyetracking Visualisation",
)


class Actuator(_Actuator):
    """Actuator base class, see `EyeActuator` and `MouseActuator` for examples."""

    def __init__(
        self,
        element_id: str,
        color: str = "red",
    ):
        """Constructor.

        Args:
            element_id (str): element to move.
            color (str, optional): colour of the element. Defaults to "red".
        """
        super().__init__()
        self.color = color
        self.xpath = f"//svg:circle[@id='{element_id}']"

    @attempt
    def close_window(self, action: WindowCloseEvent):  # noqa
        return action  # allows the program to exit

    def resize_element(self, size: float):
        """Resize the element."""
        return Update.new(xpath=self.xpath, attrs={"r": size})

    def show_element(self):
        """Show the element."""
        return Update.new(xpath=self.xpath, attrs={"fill": self.colour})

    def hide_element(self):
        """Hide the element."""
        return Update.new(xpath=self.xpath, attrs={"fill": "transparent"})


class EyeActuator(Actuator):
    """Actuator for the eyetracker."""

    @attempt
    def move_on_eyetracker(self, action: EyeMotionEvent):
        """Moves the element to the position of the eye. The element will change size depending on fixate/saccade status."""
        x, y = action.position
        actions = [Update.new(xpath=self.xpath, attrs={"cx": x, "cy": y})]
        if action.fixated:
            actions.append(self.resize_element(size=10))
            # actions.append(self.show_circle())
        else:
            actions.append(self.resize_element(size=20))
            # actions.append(self.hide_circle())
        return actions


class MouseActuator(Actuator):
    """Actuator for the mouse."""

    @attempt
    def move_on_mouse(self, action: MouseMotionEvent):
        """Moves the element to the position of the mouse."""
        x, y = action.position
        return Update.new(xpath=self.xpath, attrs={"cx": x, "cy": y})


class Avatar(_Avatar):
    """Avatar class for the eyetracking/mouse visualisation."""

    def __init__(
        self,
        window_config: WindowConfiguration,
    ):
        """Constructor.

        Args:
            window_config (WindowConfiguration): config for the UI.
        """
        super().__init__(
            sensors=[],
            actuators=[
                MouseActuator(element_id="c1", color="red"),
                EyeActuator(element_id="c2", color="blue"),
            ],
            window_config=window_config,
        )

    @observe
    def on_mouse(self, event: MouseMotionEvent):  # noqa
        self.attempt(event)  # this will forward the mouse event to the MouseActuator

    @observe
    def on_gaze(self, event: EyeMotionEvent):  # noqa
        # this will forward the eye events to the EyeActuator and apply the the view space transformation
        super().on_gaze(event)


avatar = Avatar(
    window_config=window_config,
)

eyetracking_config = EyetrackingConfiguration(
    uri=args.uri, sdk=args.sdk, moving_average_n=10, velocity_threshold=0.5
)
eyetracking_sensor = EyetrackingConfiguration.new_eyetracking_sensor(eyetracking_config)

if eyetracking_sensor is None:
    print(
        f"Eyetracking sensor is not available, it is likely that the eyetracker at {args.uri} was not found, or there is a problem with the provided sdk: {args.sdk}"
    )
else:
    avatar.add_component(eyetracking_sensor)


TASK_ID = "visualise_eyetracking"
env = MultiTaskEnvironment(avatar=avatar)
env.add_task(
    name=TASK_ID,
    path=["./"],
    agent_actuators=[],
    avatar_actuators=[],
    enable=True,
)
env.run()
