from importlib.resources import files
import json
from datetime import datetime

from jinja2 import Template
from star_ray.plugin.xml import XMLAmbient, xml_history, QueryXPath, QueryXMLTemplated

from .utils import MatbiiInternalError, MultiTaskLoader

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

    def __select__(self, action):
        # print("__SELECT__!", action)
        return super().__select__(action)

    def __update__(self, action):
        # print("__UPDATE__!", action)
        if not isinstance(action, QueryXPath):
            return  # TODO we should log this kind of event!
        return super().__update__(action)

    def kill(self):
        super().kill()
        # flush the history to disk
