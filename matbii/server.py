import json
from importlib.resources import files
from deepmerge import always_merger  # used to merge configurations
from pprint import pformat
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from star_ray import Ambient
from star_ray.agent import AgentFactory
from star_ray.plugin.web import WebServer

from .utils import (
    MatbiiInternalError,
    _LOGGER,
    DEFAULT_STATIC_PATH,
    DEFAULT_SERVER_CONFIG_FILE,
)

NAMESPACE_TEMPLATE_DATA_KEY = "namespace_template_data"
NAMESPACE = __package__


class MatbiiWebServer(WebServer):

    def __init__(self, ambient: Ambient, avatar_factory: AgentFactory):
        super().__init__(ambient, avatar_factory)
        self._namespace = NAMESPACE
        self._app.mount("/static", StaticFiles(directory=DEFAULT_STATIC_PATH))
        templates = Jinja2Templates(directory=DEFAULT_STATIC_PATH)
        scripts = [
            """<script type="module" src="/static/star_ray/websocket.js"></script>""",
            """<script type="module" src="/static/template/star_ray/handle_mouse_button.js"></script>""",
            """<script type="module" src="/static/template/star_ray/handle_keyboard.js"></script>""",
        ]
        # include star_ray javascript in the head of the root template
        templates_data = {"index.html.jinja": dict(head="\n".join(scripts), body="")}
        self.load_server_config()
        self.add_template_namespace(self._namespace, templates, templates_data)

    def load_server_config(self):
        cf = DEFAULT_SERVER_CONFIG_FILE
        _LOGGER.debug("Loading matbii server config from `%s`", cf)
        with open(str(cf), encoding="UTF-8") as fp:
            server_config = json.load(fp)
        namespace_template_data = server_config.get(NAMESPACE_TEMPLATE_DATA_KEY, None)
        if namespace_template_data is None:
            raise _invalid_config_error(cf, NAMESPACE_TEMPLATE_DATA_KEY)

        # set/merge template data
        self._templates_data = always_merger.merge(
            self._templates_data, namespace_template_data
        )
        # _LOGGER.debug("Using server config: %s", str(self._templates_data))

    def register_routes(self):
        self._app.get("/", response_class=HTMLResponse)(self.serve_index)
        return super().register_routes()

    async def serve_index(self, request: Request):
        filename = "index.html.jinja"
        config = self._get_template_configuration(self._namespace, filename)
        context = {"request": request, **config["template_data"]}
        response = config["templates"].TemplateResponse(filename, context)
        return response


def _invalid_config_error(config_file, missing_key=None):
    if missing_key:
        return MatbiiInternalError(
            f"Invalid server config in file: {config_file}, required key {missing_key} is missing."
        )
