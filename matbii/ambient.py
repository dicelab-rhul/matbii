from importlib.resources import files
from datetime import datetime
from star_ray.event import (
    Event,
    Observation,
    ErrorObservation,
    ErrorActiveObservation,
    MouseButtonEvent,
    KeyEvent,
    MouseMotionEvent,
)
from star_ray.plugin.xml import XMLAmbient, xml_history, QueryXPath

from .action import (
    ToggleLightAction,
    SetLightAction,
    SetSliderAction,
    TargetMoveAction,
    BurnFuelAction,
    PumpFuelAction,
    SetPumpAction,
    TogglePumpFailureAction,
)
from .utils import MultiTaskLoader, _LOGGER, MatbiiInternalError


NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}
VALID_USER_ACTIONS = (MouseButtonEvent, KeyEvent, MouseMotionEvent)

# TODO move this to utils._const.py?
_HISTORY_PATH = str(
    files(__package__).parent
    / "logs"
    / f"./history-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.h5"
)


@xml_history(use_disk=True, force_overwrite=False, path=_HISTORY_PATH)
class MatbiiAmbient(XMLAmbient):

    def __init__(self, agents, *args, **kwargs):
        # TODO supply arguments to the loader... rather than relying on the default values
        # we are not making full use of it here (tasks can be enabled etc.)
        xml = MultiTaskLoader().get_index()
        super().__init__(agents, *args, xml=xml, namespaces=NAMESPACES, **kwargs)

    def select(self, action):
        return super().__select__(action)

    def __select__(self, action):
        try:
            return super().__select__(action)
        except Exception as e:
            _LOGGER.exception("Error occured during select")
            return ErrorActiveObservation(exception=e, action_id=action)

    def __update__(self, action):
        try:
            return self._update_internal(action)
        except Exception as e:
            _LOGGER.exception("Error occured during update")
            return ErrorActiveObservation(exception=e, action_id=action)

    def _update_internal(self, action):
        if isinstance(action, QueryXPath):
            return super().__update__(action)
        elif hasattr(action, "to_xml_queries"):
            xml_actions = action.to_xml_queries(self.state)
            if isinstance(xml_actions, list | tuple):
                # some weirdness with list comprehension means super(MatbiiAmbient, self) is required...
                return [super(MatbiiAmbient, self).__update__(a) for a in xml_actions]
            else:
                raise MatbiiInternalError(
                    f"Ambient failed to convert action: `{action}` to XML queries, invalid return type: `{type(xml_actions)}`.",
                )
        elif isinstance(action, VALID_USER_ACTIONS):
            # TODO log these actions somewhere...
            pass
        else:
            raise MatbiiInternalError(
                f"Ambient received unknown action type: `{type(action)}`."
            )

    def kill(self):
        super().kill()
        # flush the history to disk
