import json

from star_ray.plugin.web import WebAvatar
from star_ray.plugin.xml import XMLHistorySensor, QueryXMLTemplated, QueryXML
from star_ray.agent import AgentFactory, ActiveSensor, ActiveActuator
from star_ray.event import (
    SelectResponse,
    MouseButtonEvent,
    ErrorResponse,
    UpdateResponse,
)

# On the first cycle of the avatar, it will sense the entire state of the environment, this will be sent to the server for rendering.
# there after, it will sense changes to the state via a XMLHistorySensor


class ClickLightButton(QueryXMLTemplated):

    @staticmethod
    def new(source: str, target: str) -> QueryXMLTemplated:
        # here we change the state of the light along with its fill value (to reflect the change in state).
        return QueryXMLTemplated.new(
            source,
            target,
            {
                "data-state": "{{1-data_state}}",
                "fill": "{{data_colors[1-data_state]}}",
            },
        )


class ClickSliderButton(QueryXMLTemplated):

    @staticmethod
    def new(source: str, target: str) -> QueryXMLTemplated:
        # here we change the state of the light along with its fill value (to reflect the change in state).
        return QueryXMLTemplated.new(
            source,
            target,
            {
                "data-state": "{{(data_incs - 3) //2}}",
                "y": "{{data_padding + ((data_incs - 3)//2) * data_height}}",
            },
        )


class XMLActuator(ActiveActuator):

    @ActiveActuator.attempt
    def attempt(self, action):
        if isinstance(action, MouseButtonEvent):
            target = XMLActuator._get_button_target(action.target)
            if (
                target
                and action.status == MouseButtonEvent.CLICK
                and action.button == 0  # TODO check this...
            ):
                if "light" in target:
                    return [action, ClickLightButton.new(self.id, target)]
                elif "slider" in target:
                    return [action, ClickSliderButton.new(self.id, target)]
        return [action]

    @staticmethod
    def _get_button_target(targets):
        for item in targets:
            if item.endswith("button"):
                return item
        return None


class XMLSensor(ActiveSensor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._active = True

    def __sense__(self):
        if self._active:
            self.deactivate()
            return [QueryXML.new(self.id, "root", [])]
        else:
            return []

    def activate(self):
        self._active = True

    def deactivate(self):
        self._active = False

    @staticmethod
    def get_action_from_response(response):
        # this is the data that is sent to the client upon an initial sense (on the first cycle of the avatar)
        # it contains the entire SVG code for this environment which will be subsequently updated by sensing change.
        _query = QueryXML.new(None, "root", [])
        return {"xpath": _query.xpath, "attributes": response.values[0]}


class MatbiiAvatar(WebAvatar):

    def __init__(self):
        super().__init__(
            [XMLHistorySensor(), XMLSensor()], [XMLActuator()], protocol_dtype="json"
        )

    async def __receive__(self, data):
        return await super().__receive__(data)

    async def __send__(self):
        return await super().__send__()

    async def __cycle__(self):
        await super().__cycle__()

    def _deserialise_to_mouse_event(self, action):
        return MouseButtonEvent.new(
            self.id,
            action["button"],
            (action["position"]["x"], action["position"]["y"]),
            MouseButtonEvent.status_from_string(action["status"]),
            action["targets"],
        )

    def attempt(self, action: dict[str, str]):
        # print("RECIEVED ACTION", action)
        event_type = action["event_type"]
        if event_type == "MouseButtonEvent":
            # TODO if this returns None, it was a click but not on a button,
            # this kind of event should be logged anyway! perhaps the environment should handle this? who knows...
            action = self._deserialise_to_mouse_event(action)
            self.actuators[0].attempt(action)
        else:
            raise ValueError("Received unknown user action: action")

    def perceive(self, component, observation) -> str:
        if isinstance(observation, ErrorResponse):
            print(observation)  # there was some problem!
        elif isinstance(observation, UpdateResponse):
            print(observation)  # TODO check if there was an error?
        else:  # select response
            if isinstance(component, XMLHistorySensor):
                # TODO many of these events are sent with empty responses
                # it would be much better to have a subscription mechanism for sensors rather than poll
                # TODO implement passive sensing!
                if observation.values:
                    print("PERCEIVE CHANGE: ", observation)
                    return observation.values
            elif isinstance(component, XMLSensor):
                # print("PERCEIVE RESET:", observation)
                return XMLSensor.get_action_from_response(observation)

    @staticmethod
    def get_factory():
        return _AvatarFactory()


class _AvatarFactory(AgentFactory):

    def __call__(self, *args, **kwargs):
        return MatbiiAvatar()
