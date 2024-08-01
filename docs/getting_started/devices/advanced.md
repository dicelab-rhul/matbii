
## Avatars

An [`Avatar`][icua.agent.Avatar] is a type of [`Agent`][star_ray.agent.Agent] that represents the user. It receives user input (e.g. mouse and keyboard), takes actions on the users behalf (as a result of this input) and displays the state of the environment to the user. This is how `matbii` includes a user in the agent simulation. 

## Devices & IOSensors

An `IOSensor` abstracts away from the underlying device implementation. The device class must follow the `IOSensor` API and contain the following methods: 

- `get_nowait() -> List[Event]`: poll for latest events
- `async get() -> List[Event`: poll for latest events, waits until an event is avaliable (call as `await sensor.get()`)
- `start()` : start/setup the device
- `stop()` : stop/clean up the device

The `get` or `get_nowait` methods will be polled periodically (during the avatar's cycle) and converted into observations for the agent. 
`start` will be called during [`on_add`][star_ray.agent.Component.on_add] and `stop` will be called during [`on_remove`][star_ray.agent.Component.on_remove]. An `IOSensor` is attached to the avatar agent in the usual way via [`add_component`][star_ray.agent.Agent.add_component].

If you wish to add support for a new device, see [`EyetrackerIOSensor`](icua.extras.eyetracking.EyetrackerIOSensor) for inspiration.

??? example
    ```
    from star_ray.agent import AgentRouted, IOSensor
    from star_ray.event import MouseMotionEvent

    class StubAgent(AgentRouted):

        @observe
        def on_mouse_event(self, mouse_event: MouseMotionEvent):
            print(mouse_event) # do something with the mouse event

    class StubDevice:

        def get_nowait(self) -> List[Event]:
            # get the mouse position from an actual device
            return [MouseMotionEvent(position=(0,0))]

        def start(self):
            pass 

        def stop(self):
            pass

    sensor = IOSensor(StubDevice())
    agent = StubAgent([sensor], [])
    ```

