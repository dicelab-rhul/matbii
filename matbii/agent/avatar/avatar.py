from typing import Any, List
from star_ray.plugin.web import WebAvatar, SocketSerdePydantic
from star_ray.agent import Actuator, AgentFactory, Sensor
from star_ray.event import (
    Event,
    KeyEvent,
    MouseButtonEvent,
    Observation,
    VisibilityEvent,
)
from .actuator import (
    SystemMonitoringActuator,
    TrackingActuator,
    ResourceManagementActuator,
)
from ..sensor import SVGSensor, SVGChangeSensor

# On the first cycle of the avatar, it will sense the entire state of the environment, this will be sent to the server for rendering.
# there after, it will sense changes to the state via a XMLHistorySensor

DEFAULT_KEY_BINDING = {
    "ArrowUp": "up",
    "ArrowDown": "down",
    "ArrowLeft": "left",
    "ArrowRight": "right",
}
ASWD_KEY_BINDING = {"w": "up", "s": "down", "a": "left", "d": "right"}
EVENT_TYPE_MOUSE_BUTTON = "MouseButtonEvent"
EVENT_TYPE_KEY = "KeyEvent"


class MatbiiAvatar(WebAvatar):

    def __init__(self):
        # use pydantic serialisation for events
        serde = SocketSerdePydantic(
            event_types=[MouseButtonEvent, KeyEvent, VisibilityEvent]
        )
        super().__init__(
            [SVGSensor(), SVGChangeSensor()],
            [
                SystemMonitoringActuator(),
                TrackingActuator(),
                ResourceManagementActuator(),
            ],
            serde=serde,
        )

    def handle_actuator_observation(
        self, actuator: Actuator, event: Observation
    ) -> List[Event]:
        # print(actuator, event)
        return super().handle_actuator_observation(actuator, event)

    def handle_sensor_observation(
        self, sensor: Sensor, event: Observation
    ) -> List[Event]:
        # print(sensor, event)
        return super().handle_sensor_observation(sensor, event)

    @staticmethod
    def get_factory():
        return _AvatarFactory()


class _AvatarFactory(AgentFactory):

    def __call__(self, *args, **kwargs):
        return MatbiiAvatar()
