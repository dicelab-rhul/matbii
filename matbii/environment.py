import asyncio

from star_ray import Environment

from .ambient import MatbiiAmbient
from .agent.avatar.avatar import MatbiiAvatar
from .server import MatbiiWebServer
from .agent import MatbiiAgent


class MatbiiEnvironment(Environment):

    def __init__(self, *args, wait=0.01, schedule_path=None, **kwargs):
        ambient = MatbiiAmbient([MatbiiAgent(schedule_path=schedule_path)])
        super().__init__(
            ambient,
            *args,
            wait=wait,
            **kwargs,
        )
        self._webserver = MatbiiWebServer(ambient, MatbiiAvatar.get_factory())
        self._cycle = 0

    def get_schedule(self):
        tasks = super().get_schedule()
        # run the web server :) it is running on the main thread here, so we can just run it as a task.
        # there may be more complex setups where it is run remotely... TODO think about how this might be done.
        # return tasks
        webserver_task = asyncio.create_task(self._webserver.run(port=8888))
        return [webserver_task, *tasks]

    async def step(self) -> bool:
        self._cycle += 1
        # return False if the simulation should stop? TODO more info might be useful...
        agents = self._ambient.get_agents()
        await self._step(agents)
        return True
