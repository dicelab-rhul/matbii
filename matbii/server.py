from importlib.resources import files
from typing import List
from dataclasses import dataclass, astuple
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from star_ray import Ambient, Environment, ActiveActuator, ActiveSensor
from star_ray.event import SelectResponse, Event

from star_ray.agent import AgentFactory
from star_ray.plugin.web import WebServer, WebAvatar
import asyncio
import pathlib


from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from .error import MatbiiInternalError


class MatbiiWebServer(WebServer):

    NAMESPACE = "matbii"

    def __init__(self, ambient: Ambient, avatar_factory: AgentFactory):
        super().__init__(ambient, avatar_factory)
        self._namespace = MatbiiWebServer.NAMESPACE
        static_path = files(__package__).parent / "static"
        self._app.mount("/static", StaticFiles(directory=static_path))
        templates = Jinja2Templates(directory=static_path)
        scripts = [
            """<script type="module" src="/static/star_ray/websocket.js"></script>""",
            """<script type="module" src="/static/template/star_ray/handle_mouse_button.js"></script>""",
        ]
        # include star_ray javascript in the head of the root template
        templates_data = {"index.html.jinja": dict(head="\n".join(scripts), body="")}
        self.add_template_namespace(self._namespace, templates, templates_data)

    def register_routes(self):
        self._app.get("/", response_class=HTMLResponse)(self.serve_index)
        return super().register_routes()

    async def serve_index(self, request: Request):
        filename = "index.html.jinja"
        config = self._get_template_configuration(self._namespace, filename)
        context = {"request": request, **config["template_data"]}
        response = config["templates"].TemplateResponse(filename, context)
        return response
