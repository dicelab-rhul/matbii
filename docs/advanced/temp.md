
However if you wish to implement a custom entry point, or wish to understand the inner workings of `matbii` a bit better then read on. 

## Guidance

One class of experiments that `matbii` aims to support are those relating to _attention guidance_. This is done via with guidance agents. The goal of these agents is to assist the user in managing or completing one or more tasks by provide guidance or _feedback_ to them in some form. As usual, the guidance agents follow a sense/decide/act loop:

- **Sense**: gather information about their environment via their sensors (e.g. user input and the state of the `matbii` UI)
- **Decide**: whether to display guidance based on this information.
- **Act**: Provide feedback to the user e.g. by modifying the UI, playing a sound, etc.

Of course you are free to implement an agent that aims to acheive this goal how ever you'd like, but `matbii` has support for task-based visual guidance with [`icua.agent.GuidanceAgent`][icua.agent.GuidanceAgent]. This class defines some useful methods and a convenient sensors-actuator API which will make developing guidance agents more straight-forward. 

### Sensors & Task Acceptability 

We assume that each task may be in one of two states - _acceptable_ or _unacceptable_. Acceptable means that the user does not need to do anything for this task. Unacceptable means that the attention of the user is required and that there is likely some action they need to take - this is when the guidance agent (may) need to intervene and provide feedback to the user. 

To keep things modular, task acceptability is tracked and managed by the agent's sensors, any sensor which implements: [icua.agent.TaskAcceptabilitySensor][icua.agent.TaskAcceptabilitySensor] may be used for this. 

Each of the tasks implemented in `matbii` has an associated task acceptability sensor:

- [`SystemMonitoringTaskAcceptabilitySensor`][matbii.guidance.SystemMonitoringTaskAcceptabilitySensor]
- [`ResourceManagementTaskAcceptabilitySensor`][matbii.guidance.ResourceManagementTaskAcceptabilitySensor]
- [`TrackingTaskAcceptabilitySensor`][matbii.guidance.TrackingTaskAcceptabilitySensor]

### Guidance decision making

[`GuidanceAgent`][icua.agent.GuidanceAgent] defines four methods which will be called as a direct result of a change in _acceptability_ or in _activity_. Task activity determines whether the task is current active in the environment. A task may be considered inactive if it is not accepting user interaction for what ever reason (e.g. if by design it not currently being displayed to the user). 

- `on_acceptable(self, task: str)`
- `on_unacceptable(self, task: str)`
- `on_active(self, task: str)`
- `on_inactive(self, task: str)`

where `task` is the name of the task. Guidance agents also automatically record user input which is made accessible via the `get_latest_user_input(self, event_type: type, n: int = 1) -> Iterator[Event]` method, see [devices and user input](getting_started/devices) for details on which `event_types` are accepted.

??? quote "Example"
    === "`agent.py`"
        ```
        from icua.agent import GuidanceAgent
        from icua.event import MouseMotionEvent

        class MyGuidanceAgent(GuidanceAgent):

            def on_unacceptable(self, task: str):
                # assumes task is always active
                target = self.get_latest_user_input(MouseMotionEvent)[0].target
                if task in target: # the user is attending this task
                    self.guidance_actuator.hide_guidance()
                else:
                    self.guidance_actuator.show_guidance()
        ```
    === "`main.py`"
        from .agent import MyGuidanceAgent, MyGuidanceActuator, MyGuidanceSensor
        from .tasks import MyTask









### Actuators & Visual Feedback

!!! failure "COMING SOON"

### Counter-factual guidance

!!! failure "COMING SOON"

## Multi-tasking

!!! failure "COMING SOON"

### Multi-task Environment

!!! failure "COMING SOON"

### Task control

!!! failure "COMING SOON"

## Post-Analysis

!!! failure "COMING SOON"





