

# Configuration

`matbii` is highly configurable thanks to the modular agent-based design of `icua`. Various files are used in the configuration of tasks and experiments, these files are described in the sections below. See [this example](#default-entry-point-example) for usage with the default entry point.

{{ default_entry_config() }}

-----------------------------

## Task Configuration

Along with the main configuration which provides some general options for configuring experiments the tasks themselves can be configured. Task configuration is independent of the entry point. 

There are two types of task configuration files:

- State files (`.json`)
- Schedule files (`.sch`)

For a single experiment these files will all be placed in a single directory, for example: 
```
experiment/
 ├─resource_management.json  
 ├─resource_management.sch  
 ├─system_monitoring.json  
 ├─system_monitoring.sch  
 ├─tracking.json  
 └─tracking.sch
```

The directory `experiment` will be used as the `experiment.path` option in the [main configuration file](#experiment-configuration). You may or may not decide to place the main configuration inside this directory. It is often better to provide an absolute path in `experiment.path` to avoid issues with path resolution (recall that the configuration path is relative to the working directory - where `python -m matbii -c <CONFIG>` is run).

### State files

State files contain values that determine the starting state of the task and influence how the task is displayed in the UI. Options are described below.

??? quote "Resource Management Task Configuration"
{% include 'getting_started/resource_management_config.md' %}

??? quote "System Monitoring Task Configuration"
{% include 'getting_started/system_monitoring_config.md' %}

??? quote "Tracking Task Configuration"
{% include 'getting_started/tracking_config.md' %}



### Schedule files

Schedule files determine how each task evolves, the files are written in a DSL (domain specific language) details of which can be found [here](https://github.com/BenedictWilkins/pyfuncschedule).

Briefly, schedule files contain a list of actions with times to execute them. Each line of a configuration file follows a template:
```
ACTION(...) @ [T1, T2, ...] : R
```

Where `T1`, `T2`, ... are times to wait before executing the action `ACTION`, and `R` is the number of times to repeat the given sequence of wait times, the special character `*` means repeat forever. 

Each task has a number of actions that have been defined which will update the task's state. 

#### Actions

Actions are defined in `Actuator`s which form part of the task definition.

!!! failure "ACTION DOCUMENTATION COMING SOON"
    For now see [example schedules](#example-schedules)
    
#### Timing functions 

Timings can be specified explicitly as constant `int` or `float` values (seconds).

!!! quote "example"
    ```
    toggle_light(1) @ [10]:*
    ```
    This will toggle light number 1 on/off every 10 seconds.

but we may want some more complicated schedule. This can be acheived using some built-in timing functions to introduce randomness or otherwise.

- `uniform(a : int, b : int)` - a random integer between a and b (inclusive).
- `uniform(a : float, b : float)` - a random float between a and b (inclusive).

!!! quote "example"
    ```
    toggle_light(1) @ [uniform(10,20)]:*
    ```
    This will toggle light number 1 on/off at times randomly chosen between 10 and 20 seconds.

We can build more complex schedules that mix timing functions and constant values. 

!!! quote "example"
    ```
    toggle_pump_failure("ab") @ [uniform(3,10), 2]:*
    ```
    This will trigger a pump failure for 2 seconds after some random time between 3-10 seconds and repeat.

#### Example Schedules

??? quote "Tracking Task Schedule"
    ```
    # this moves the target around randomly by 5 units every 0.1 seconds
    perturb_target(5) @ [0.1]:*
    ```

??? quote "System Monitoring Task Schedule"
    ```
    # this makes the lights turn to their unacceptable state every 10-20 seconds
    off_light(1) @ [uniform(10,20)]:*    # this means failure for light 1
    on_light(2) @ [uniform(10,20)]:*     # this means failure for light 2
    # toggle_light(1) is also an option
    # toggle_light(2) is also an option

    # this randomly moves the sliders (up/down by 1) every 5-6 seconds.
    perturb_slider(1) @ [uniform(5,6)]:*
    perturb_slider(2) @ [uniform(5,6)]:*
    perturb_slider(3) @ [uniform(5,6)]:*
    perturb_slider(4) @ [uniform(5,6)]:*
    ```

??? quote "Resource Management Task Schedule"
    ```
    # these determine pump failures, fail for 2 seconds after between 3 and 10 seconds (and repeat)
    toggle_pump_failure("fd") @ [uniform(3,10), 2]:*
    toggle_pump_failure("fb") @ [uniform(3,10), 2]:*
    toggle_pump_failure("db") @ [uniform(3,10), 2]:*
    toggle_pump_failure("ec") @ [uniform(3,10), 2]:*
    toggle_pump_failure("ea") @ [uniform(3,10), 2]:*
    toggle_pump_failure("ca") @ [uniform(3,10), 2]:*
    toggle_pump_failure("ba") @ [uniform(3,10), 2]:*
    toggle_pump_failure("ab") @ [uniform(3,10), 2]:*

    # these determine the burning of fuel in the two main tanks
    burn_fuel("a", 10) @ [0.1]:*
    burn_fuel("b", 10) @ [0.1]:*

    # these determine the flow of the pumps (when they are "on")
    pump_fuel("fd", 20) @ [0.1]:*
    pump_fuel("fb", 20) @ [0.1]:*
    pump_fuel("db", 20) @ [0.1]:*
    pump_fuel("ec", 20) @ [0.1]:*
    pump_fuel("ea", 20) @ [0.1]:*
    pump_fuel("ca", 20) @ [0.1]:*
    pump_fuel("ba", 20) @ [0.1]:*
    pump_fuel("ab", 20) @ [0.1]:*
    ```

## Usage

### Default entry point

!!! example "Default entry point"
    An example of all files discussed above can be found [here](https://github.com/dicelab-rhul/matbii/tree/main/example).
    
    To run the example, [install matbii locally](index.md#install).

    Navigate to the `example` directory:
    ```
    cd matbii/example
    ```
    and run:
    ```
    python -m matbii -c experiment-C.json
    ```

### Custom entry point

!!! failure "Custom entry point"
    DOCUMENTATION COMING SOON