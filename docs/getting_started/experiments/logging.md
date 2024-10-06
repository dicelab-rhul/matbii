
`matbii` logs all events in the simulation to a file as they happen. This file can be configured in the [main configuration](getting_started/configuration.md) under the `logging.path`. 

## Log file structure

Each line of the log file contains data for a single event and has the following format:

```
TIMESTAMP EVENT_TYPE EVENT_DATA
```

- `TIMESTAMP` is the time that the event was logged, this is very close to the time that the event occurs in the simulation, logging happens immediately **before** an event is executed. This timestamp gives the most accurate timing information for when a state change was made. For [device related events](#device) it may be better to use the instantiation time (part of `EVENT_DATA`) to get for example, the time at which a user reacted to a given stimulous. In most cases the difference in these timestamps is very minimal (0.1-1 millisecond)

- `EVENT_TYPE` is the type of event that was executed (the name of the event class), for a full list of these types, see [Event Types](#event-types)

- `EVENT_DATA` a JSON representation of the data associated with the event (enclosed in `{` `}`). The event data will contain at the very least, a unique `id` for the event and a `timestamp` for when the event was instantiated. 

We provide a parser for these files will which reconstruct the origin event class, see [Post Analysis](post-analysis.md).

## Event types

You can expect to see various kinds of events in a log file, the types are documented in the [API reference](/matbii/reference/). 

### Actions

All actions that modify the state are recorded.

Some actions are task specific, for example:

- System Monitoring: `SetLightAction`, `ToggleLightAction`, `SetSliderAction`
- Resource Management: `BurnFuelAction`, `PumpFuelAction`, `TogglePumpAction`, `SetPumpAction`
- Tracking: `TargetMoveAction`

Some actions are due to guidance, for example: `DrawBoxAction`, `DrawArrowAction`, `HideElementAction`, `ShowElementAction`

### Primitive Actions

Primitive events typically represent changes made internally by `matbii` or parent packages (`icua` or `star-ray`), for example when initially configuring the UI. These include: `Update, Insert, Replace, Delete` which are used to directly modify the state of `matbii`.

### Device

Events that come from devices are also recorded and include: `KeyEvent, MouseButtonEvent, MouseMotionEvent, EyeMotionEvent, WindowMoveEvent, WindowResizeEvent, WindowFocusEvent, WindowOpenEvent, WindowCloseEvent`, see [device documentation](/matbii/getting_started/devices/index.md) for details of each event.

### Flags

Flag events are used to indicate state changes that may be of interest during post analysis. These events typically do not modify the state themselves, but indicate that some important change has occured. 

- `RenderEvent` : the UI has been refreshed and that any changes are now visible to the user.
- `TaskAcceptable` : the [Guidance Agent](index.md) has determined that a task has entered an acceptable state (according to its decision rules).
- `TaskUnacceptable` : the [Guidance Agent](index.md) has determined that a task has entered an unacceptable state (according to its decision rules).

- `ShowGuidance` : the guidance agent has decided to show guidance on a task.
- `HideGuidance` : the guidance agent has decided to hide guidance on a task.

## Gotchas

Below is a list of [Gotchas](https://en.wikipedia.org/wiki/Gotcha_(programming)) that you should be aware of when working with log files and interpreting the results. 

### Task acceptability

The two flag events `TaskAcceptable` and `TaskUnacceptable` occur AFTER a task has reached an acceptable/unacceptable state. The agent requires 1 cycle to observe the state, decide it is acceptable/unacceptable and then act to produce the corresponding flag event. Using the timestamps of these events to classify other events as occuring when a task is acceptable/acceptable may lead to off-by-one errors. The analysis functions provided for analysis take this into account and are reliable for doing this classification.

### Order of execution

You should not rely on the order of the execution of the agents (within a single cycle) when analysis event timestamps since this is undefined, all events that appear between two `RenderEvents` should be considered as happening simultaneously, at least from the perspective of the user. This effectively splits up the event stream into small discrete chunks and sets a limit on the accuracy of the timing information.