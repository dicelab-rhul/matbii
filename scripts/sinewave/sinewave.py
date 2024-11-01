"""Simple example that animates a circle moving along a sine wave."""

from icua import MultiTaskEnvironment
from icua.agent import Actuator, Avatar, AvatarActuator, attempt
from icua.config import WindowConfiguration

from star_ray_xml import Update
from star_ray.utils import _LOGGER

import time
import math

# silence logs from star_ray
_LOGGER.setLevel("WARNING")

# configuration of the UI window
window_config = WindowConfiguration(
    width=640,
    height=640,
    title="Sinewave",
)


# the actuator which will update the circles position
class SinewaveActuator(Actuator):  # noqa
    @attempt
    def sinewave(self):  # noqa
        sine_wave = (1 + math.sin(time.time())) / 2
        y = window_config.height * sine_wave
        xpath = "//svg:circle[@id='c1']"
        return Update.new(xpath=xpath, attrs={"cy": y})


avatar = Avatar(
    sensors=[],  # mouse, keyboard and window controls will be captured by default
    actuators=[
        AvatarActuator()  # The AvatarActuator forwards user input to the environment
    ],
    window_config=window_config,
)

# create our environment
env = MultiTaskEnvironment(
    avatar=avatar,
    wait=0.0,  # simulate as fast as possible
    svg_size=(window_config.width, window_config.height),
)

# add the task to the environment
env.add_task(
    name="sinewave",  # task name (used to find files .svg and .sch)
    path=["./"],  # set path for task files
    agent_actuators=[SinewaveActuator],  # task specific actuators
    avatar_actuators=[],
    enable=True,
)
env.run()
