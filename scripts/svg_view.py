from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from jinja2 import Template
from pathlib import Path
import json

app = FastAPI()

# Sample HTML content for testing
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>SVG Renderer</title>
</head>
<body>
    <h1>SVG Live Renderer</h1>
    <div id="svg-container">SVG will be displayed here.</div>
    <script>
        var ws = new WebSocket("ws://localhost:8181/ws");
        ws.onmessage = function(event) {
            console.log(event);
            var svgContainer = document.getElementById('svg-container');
            svgContainer.innerHTML = event.data;
        };
    </script>
</body>
</html>
"""


class SVGFileWatcher(FileSystemEventHandler):
    def __init__(self, websocket: WebSocket, loop):
        self.websocket = websocket
        self.loop = loop

    def on_modified(self, event):
        if event.src_path.endswith(".svg") or event.src_path.endswith(".json"):
            asyncio.run_coroutine_threadsafe(self.send(event.src_path), self.loop)

    async def send(self, path: str):
        path = Path(path)
        with open(path.with_suffix(".svg"), "r") as svg_file:
            with open(path.with_suffix(".json")) as json_file:
                data = json.load(json_file)
                svg_content = Template(svg_file.read()).render(**data)
                await self.websocket.send_text(svg_content)


@app.get("/")
async def get():
    return HTMLResponse(html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_running_loop()
    event_handler = SVGFileWatcher(websocket=websocket, loop=loop)
    path = os.path.dirname(__file__)
    observer = Observer()
    observer.schedule(event_handler, path=path, recursive=False)
    observer.start()
    await event_handler.send(path + "/test.svg")

    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8181)
