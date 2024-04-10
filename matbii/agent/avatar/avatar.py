from typing import List
from star_ray.plugin.web import WebAvatar, SocketSerdePydantic
from star_ray.plugin.xml import QueryXML
from star_ray.agent import Actuator, AgentFactory, ActiveSensor, ActiveActuator, Sensor
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
from .sensor import SVGSensor, SVGChangeSensor

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
        print(actuator, event)
        return super().handle_actuator_observation(actuator, event)

    def handle_sensor_observation(
        self, sensor: Sensor, event: Observation
    ) -> List[Event]:
        print(sensor, event)
        return super().handle_sensor_observation(sensor, event)

    # async def __cycle__(self):
    #     await super().__cycle__()

    # def attempt(self, action: dict[str, str]):
    #     # print("RECIEVED ACTION", action)
    #     event_type = action["event_type"]
    #     if event_type == EVENT_TYPE_MOUSE_BUTTON:
    #         action = self._deserialise_to_mouse_event(action)
    #     elif event_type == EVENT_TYPE_KEY:
    #         action = self._deserialize_to_keyboard_event(action)
    #     else:
    #         _LOGGER.warning("Avatar received unknown user action: %s", action)
    #         return

    #     for actuator in self.actuators:
    #         actuator.attempt(action)

    # def perceive(self, component, observation) -> str:
    #     if isinstance(observation, ErrorResponse):
    #         print(observation)  # there was some problem!
    #     elif isinstance(observation, UpdateResponse):
    #         print(observation)  # TODO check if there was an error?
    #     else:  # select response
    #         if isinstance(component, XMLHistorySensor):
    #             # TODO many of these events are sent with empty responses
    #             # it would be much better to have a subscription mechanism for sensors rather than poll
    #             # TODO implement passive sensing!
    #             if observation.values:
    #                 # print("PERCEIVE CHANGE: ", observation)
    #                 return observation.values
    #         elif isinstance(component, XMLSensor):
    #             # print("PERCEIVE RESET:", observation)
    #             return XMLSensor.get_action_from_response(observation)

    @staticmethod
    def get_factory():
        return _AvatarFactory()


class _AvatarFactory(AgentFactory):

    def __call__(self, *args, **kwargs):
        return MatbiiAvatar()
