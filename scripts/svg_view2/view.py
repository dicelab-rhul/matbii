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

from matbii.utils import MultiTaskLoader

STATIC_PATH = "/home/ben/Documents/repos/dicelab/icua2/matbii/static/"


class SVGFileWatcher(FileSystemEventHandler):
    def __init__(self, websocket: WebSocket, loop):
        self.websocket = websocket
        self.loop = loop
        INDEX_FILE = STATIC_PATH + "index.svg.jinja"
        TASK_PATH = STATIC_PATH + "task"
        self.loader = MultiTaskLoader(index_file=INDEX_FILE, task_path=TASK_PATH)

    def on_modified(self, event):
        asyncio.run_coroutine_threadsafe(self.send(), self.loop)

    async def send(self):
        self.loader.load()
        svg_content = self.loader.get_index()
        await self.websocket.send_text(svg_content)


@app.get("/")
async def get():
    return HTMLResponse(html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_running_loop()
    event_handler = SVGFileWatcher(websocket=websocket, loop=loop)
    observer = Observer()
    observer.schedule(event_handler, path=STATIC_PATH, recursive=True)
    observer.start()
    await event_handler.send()

    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8181)
