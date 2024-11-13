"""Eyetracking visualisation.

This will create an avatar that displays the mouse and gaze location of the user. It may be used for debugging purposes, or to choose suitable parameters for a new eyetracker.

The eyetracking position is represented as a blue dot, the mouse position is a red dot.
The blue dot will change its size depending on fixation/saccade. Small for fixation, large for saccade.

If the eyetracker fails to load you will get a message in the console saying so (its probably a URI issue, make sure you get it from your eyetracker manager and the eyetracker has been calibrated and is on.)
"""

from star_ray_xml import Update
from star_ray.utils import _LOGGER

from icua import MultiTaskEnvironment
from icua.agent import Avatar as _Avatar, Actuator as _Actuator, attempt, observe
from icua.event import MouseMotionEvent, EyeMotionEvent, WindowCloseEvent
from matbii.config import EyetrackingConfiguration, WindowConfiguration
import argparse


# silence logs from star_ray logger
_LOGGER.setLevel("WARNING")

argparser = argparse.ArgumentParser()
argparser.add_argument(
    "--uri",
    type=str,
    help="The uri (address) of the eye tracker device, e.g. `tet-tcp://169.254.126.68`",
)
argparser.add_argument(
    "--sdk", type=str, default="tobii", help="The sdk to use, defaults to `tobii`."
)
argparser.add_argument("--ma", type=int, default=10, help="Moving average n")
argparser.add_argument(
    "--vt", type=float, default=0.5, help="velocity threshold (normalised screen space)"
)
argparser.add_argument("--fullscreen", "-f", action="store_true")

args = argparser.parse_args()

window_config = WindowConfiguration(
    width=640,
    height=640,
    fullscreen=args.fullscreen,
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
    uri=args.uri,
    sdk=args.sdk,
    moving_average_n=args.ma,
    velocity_threshold=args.vt,
    enabled=True,
)
eyetracking_sensor = EyetrackingConfiguration.new_eyetracking_sensor(eyetracking_config)

if eyetracking_sensor is None:
    print(
        f"Eyetracking sensor is not available, it is likely that the eyetracker at {args.uri} was not found, or there is a problem with the provided sdk: {args.sdk}"
    )
else:
    avatar.add_component(eyetracking_sensor)


TASK_ID = "visualise_eyetracking"
if window_config.fullscreen:
    svg_size = (
        1920,
        1080,
    )  # this is monitor specific, change it if things break! TODO use pygame to get the window size...
else:
    svg_size = (window_config.width, window_config.height)

env = MultiTaskEnvironment(
    avatar=avatar,
    svg_size=svg_size,  # resize the svg to fit whatever the window size is...
)
env.add_task(
    name=TASK_ID,
    path=["./"],
    agent_actuators=[],
    avatar_actuators=[],
    enable=True,
)
env.run()
