from importlib.resources import files
import json
from datetime import datetime

from .action import ToggleLightAction, SetLightAction, SetSliderAction, TargetMoveAction

from star_ray.plugin.xml import XMLAmbient, xml_history, QueryXPath

from .utils import MultiTaskLoader, _LOGGER


NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}

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
        self._valid_actions = (
            ToggleLightAction,
            SetLightAction,
            SetSliderAction,
            TargetMoveAction,
        )

    def __select__(self, action):
        return super().__select__(action)

    def __update__(self, action):
        if isinstance(action, QueryXPath):
            return super().__update__(action)
        elif isinstance(action, self._valid_actions):
            return super().__update__(action.to_xml_query(self))
        else:
            _LOGGER.debug("UNKNOWN ACTION TYPE: %s", repr(action))
            return  # TODO we should log this kind of event!

    def kill(self):
        super().kill()
        # flush the history to disk
