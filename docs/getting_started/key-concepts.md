This page presents some key concepts and explains terminology used in the [getting started guide](./index.md), if you are confident that you understand these or are in a rush then please skip to [Configuration](./configuration.md) and refer back if needed.

### Environment

The environment contains all of the [agents](#agent), [tasks](#task), and a [state](#state), and is responsible for running the simulation. `matbii` relies on the [agent](#agent)-based abstractions provided by the [`star-ray`](https://github.com/dicelab-rhul/star-ray) and [`icua`](https://github.com/dicelab-rhul/icua2) packages. It is at its heart an multi-[agent](#agent) simulation that includes the _user_ as one of these [agent](#agent). 

### State

The state of `matbii` is represented using [XML](https://en.wikipedia.org/wiki/XML), more specifically using [SVG](https://en.wikipedia.org/wiki/SVG). The state represents all of the persistent data in the `matbii` environment, [agents](#agent) have access to this data via their [sensors](#sensor) and can modify it using their [actuators](#actuator). The state is represented internally as a data structure which can be queried using [XPATH](https://en.wikipedia.org/wiki/XPath), [actions](#action) are compiled queries that read or write XML data. 

Part of what makes `matbii` so configurable is that User Interface (UI) data is represented directly as part of the state. This is a departure from the more common [Model-View-Controller (MVC)](https://en.wikipedia.org/wiki/Model–view–controller) architecture where there is clearer seperation between the model (the state) and the view (the UI). The benefit of this architecture is that [agents](#agent) can directly modify the UI. This will happen as part of the normal running of the system (e.g. when updating a [task](#task)) or when providing [visual feedback or guidance](#guidance-agents) to the user. In short, it enables maximum flexiblity and scope for experimentation with different kinds of visual feedback. It also makes the process of add new tasks or developing new multi-task systems more straightforward (see [advanced topics](../advanced/index.md)for details).

### Task

`matbii` is a multi-task application originally designed as a platform for human attention research. Tasks require the user to perform some actions to solve, or in this case, continually manage their state and are typically indepedent from each other. Some tasks may be more challenging to manage than others, and typically a human user will struggle to address or interact with multiple tasks simultaneously. Instead, they will likely switch between them allocating bursts of attention. The strategies or mechanisms that humans employ to do this are of significant interest to attention research and have motivated the development of platforms such as `matbii`.

This version of `matbii` currently defines three tasks (a subset of the five tasks originally implemented in NASA's MATB-II system):

- [`tracking`](#tracking)
- [`system monitoring`](#system-monitoring)
- [`resource management`](#resource-management)

The goals of a user in each of these tasks is outlined below.

#### Tracking

The user is tasked with keeping a target (1) within a central box (2) using the arrow keys on a keyboard. The target will move around according to the task [schedule](configuration.md#schedule-files). 

<img src="https://via.placeholder.com/150" alt="Placeholder image">

#### System Monitoring

The user is tasked with clicking on lights (1, 2) and sliders (3) to keep them in the acceptable state. 

- light (1) should be kept on (green by default), grey represents the off state (unacceptable).
- light (2) should be kept off (grey by default), red represents the on state (unacceptable).

Lights will toggle on/off on click.

- sliders (3) should be kept in the central position, they will move to this position on click.

The lights and sliders will change their state according to the task [schedule](configuration.md#schedule-files).

<img src="https://via.placeholder.com/150" alt="Placeholder image">

#### Resource Management

The user is tasked with keeping the fuel main fuel tanks in the acceptable range (1, 2). The fuel in these tanks will be slowly burned and reduce overtime. Fuel can be transfered between tanks by clicking on pumps (3), this will begin the transfer of fuel at a given rate. Pumps will periodically fail (4) rendering them unusable, fuel will stop flowing if a pump is the failure state.

Pump failure, fuel transfer and burn happen according to the task [schedule](configuration.md#schedule-files).  

<img src="https://via.placeholder.com/150" alt="Placeholder image">

### Agent

`matbii` follows an agent-based architecture, virtually everything is done by agents - updating tasks, providing guidance to a user, displaying the UI and putting user input to use (see [Avatar](#avatars)). There are many definitions of what an [agent](https://en.wikipedia.org/wiki/Software_agent) _is_, but for our purposes it is a persistent and modular piece of software that makes decisions which influence its [environment](#environment) or other agents. An agent typically has a collection of [sensors](#sensor) and a collection of [actuators](#actuator) which permit certain affordances, that is, allow it to take certain [actions](#action) and [observe](#observation) certain outcomes in pursuit of some goal. Goals may be more or less sophisticated and `matbii` has the full range. 

#### Task Agents

Each [task](#task) in `matbii` is managed by an agent, its goal is to make modifications to its assigned task in line with the task definition. In practice, the task definition is implemented as part of the agents behaviour - it decides when and how to update the task. A [task](#task) is therefore defined by its [state](#state), the assigned agent, and the [Avatar](#avatars) which defines how the user interacts with a specific task (see also advanced topic: [developing new tasks](../advanced/index.md)). This goal is fairly simple and doesn't typically require reasoning or other higher functions.

#### Guidance Agents

The goal of the guidance agent on the other hand is more demanding, it is to decide when and how to prompt a human user into addressing a particular task, for example, to ensure that no task is neglected, or to ensure "optimal" allocation of attention. The best way to do this is an open question since we still don't fully understand the the mechanisms that drive our attention. There are many questions brought up by the design a guidance agent, experimenting with goals/behaviours here may give insight into the our attention mechanisms, this is what has motivated the development of this system.

#### Avatars

An avatar is a special kind of agent which acts on behalf of the user, think of an avatar as your virtual double. It captures input from periferal devices (mouse, keyboard, eyetracker, etc.) and performs [actions](#action) on your behalf. There is a mapping from user input to tasks-specific [actions](#action) which it uses to do so. This mapping forms part of the [task](#task) definition and is implemented as a task-specific [actuator](#actuator). The avatar also provides its own [observations](#observation) to the user in a human-friendly fashion, in this case, it observes the state of the [environment](#environment) (the SVG data) and displays it in a window. Avatars don't have their own goals, they instead act as a bridge between the real world and virtual environment making your goals _their_ goals.

#### Actuator

An actuator is an interface between an [agent](#agent) and its [environment](#environment), it allows the agent to have tangible influence of the [state](#state) of its [environment](#environment). The real world analogue are your muscles, or your hands. They enable you to take certain situation-dependent [actions](#action) and to acheive your goals. 

#### Sensor

A sensor is an interface between an [agent](#agent) and its [environment](#environment) which allows the agent to [observe](#observation) the [state](#state) of its [environment](#environment). Sensors do not have influence over the [state](#state), but instead provide information crucial to the acheivement of an [agents](#agent) goals. 


#### Action

An action is a discrete event or query which will modify (in the case of an [actuator](#actuator)) or retrieve 
(in the case of a [sensor](#sensor)) data from the [environment](#environment) [state](#state).

#### Observation

An observation is typically the result of an [action](#action), it contains data that an [agent](#agent) may use to make its decisions or review its beliefs. Typically observations are recived by [sensors](#sensor) as a result of a sensing action, but [actuators](#actuator) may also received them - think of the strain feedback your hand may give you when doing something strenuous.
