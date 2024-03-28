from importlib.resources import files
import json
from datetime import datetime

from jinja2 import Template
from star_ray.plugin.xml import XMLAmbient, xml_history, QueryXPath, QueryXMLTemplated

from .error import MatbiiInternalError

_STATIC_PATH = files(__package__).parent / "static"
_XML_TEMPLATE_PATH = _STATIC_PATH / "matbii.svg.jinja"
_XML_TEMPLATE_DATA_PATH = _STATIC_PATH / "matbii.json"
NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}

_HISTORY_PATH = str(
    files(__package__).parent
    / "logs"
    / f"./history-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.h5"
)


@xml_history(use_disk=True, force_overwrite=False, path=_HISTORY_PATH)
class MatbiiAmbient(XMLAmbient):

    def __init__(self, agents, *args, **kwargs):
        xml = self.load_xml_template(
            _XML_TEMPLATE_PATH, template_data_path=_XML_TEMPLATE_DATA_PATH
        )
        super().__init__(agents, *args, xml=xml, namespaces=NAMESPACES, **kwargs)

    def load_xml_template(
        self, template_path, template_data=None, template_data_path=None
    ):
        if template_data is None:
            if template_data_path is None:
                raise MatbiiInternalError(
                    "One of `template_data` or `template_data_path` must be specified."
                )
            with open(template_data_path, "r", encoding="UTF-8") as json_file:
                template_data = json.load(json_file)

        with open(template_path, "r", encoding="UTF-8") as svg_file:
            template = svg_file.read()

        template = Template(template)
        return template.render(**template_data)

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
