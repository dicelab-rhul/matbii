

# Configuration

`matbii` is highly configurable thanks to the modular agent-based design of `icua`. Various files are used in the configuration of tasks and experiments, these files are described in the sections below.

{# COMMENT: this section is generated by the macro in /scripts/docs/macros.py #}

## Main Configuration 

Matbii can be configured using a `.json` file.

The path of this file is supplied as `-c <CONFIG_PATH>`, for example:

```
python -m matbii -c ./experiment-config.json
```

The default entry point (main) configuration has sections corresponding to a specific aspect of the simulation. Not all options need to be specified and all have reasonable default values.

{{ default_entry_config() }} 

!!! note "Custom entry points"
    The main configuration outlined here is used in the default entry point (`main.py`), but may also be useful for [custom entry points](../advanced/custom_entry_points.md). Other entry points include `--example <EXAMPLE>` (see [here](#quick-start)), and `--script <SCRIPT>`, (see [here](./experiments/post-analysis.md)).


### Command line overrides

It is possible to override the configuration options via the command line using:

```--config.*KEYS *VALUES```

where `*KEYS` is a dot seperated path to the configuration option you wish to override, and `*VALUES` is one of more (space separated) values for the option. For example:
```
--config.experiment.id 'experiment-1'
```
Values must be valid python literals (str, int, float, bool, list, tuple, dict). String values must be surrounded by single quotes.

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

The directory `experiment` above should be used as the `experiment.path` option in the [main configuration file](#main-configuration). You may or may not decide to place the main configuration inside this directory. Either way, it is better to provide an absolute path in `experiment.path` to avoid issues with path resolution (recall that the configuration path is relative to the working directory - where `python -m matbii -c <CONFIG>` is run).

#### Naming convention

Each configuration file must be named after the task (as above): `resource_management`, `system_monitoring`, `tracking` with `.json` for state files and `.sch` for schedule files. These names are also used when enabling a task in the [main configuration file](#main-configuration).

#### Default configuration

All tasks have a [default configuration](https://github.com/dicelab-rhul/matbii/tree/main/matbii/tasks) which will be used in place of state or schedule if the file is not given. Each of the files above is overriding the default state or schedule for the corresponding task.

### State files

State files contain values that determine the starting state of the task and influence how the task is displayed in the UI. Options are described below.

??? info "Resource Management Task Configuration"
{% include 'getting_started/resource_management_config.md' %}

??? info "System Monitoring Task Configuration"
{% include 'getting_started/system_monitoring_config.md' %}

??? info "Tracking Task Configuration"
{% include 'getting_started/tracking_config.md' %}


### Schedule files

Schedule files determine how each task evolves, the files are written in a DSL (Domain Specific Language) details of which can be found [here](https://github.com/BenedictWilkins/pyfuncschedule).

Briefly, schedule files contain a list of actions with times to execute them. Each line of a configuration file follows a template:
```
ACTION(...) @ [T1, T2, ...] : R
```

Where `T1`, `T2`, ... are times to wait before executing the action `ACTION`, and `R` is the number of times to repeat the given sequence of wait times, the special character `*` means repeat forever. 

Each task has a number of actions that have been defined which will update the task's state. 

#### Actions

Actions make a change to the state of `matbii` and have their own internal definition. The full list of actions avaliable for use in a schedule is given below. Some examples are given in the [next section](#timing-functions).

??? info "Action Reference"
    **Tracking**

    {{indent(list_attempt_methods("matbii.tasks.TrackingActuator"))}}

    **System Monitoring**

    {{indent(list_attempt_methods("matbii.tasks.SystemMonitoringActuator"))}}

    **Resource Management**

    {{indent(list_attempt_methods("matbii.tasks.ResourceManagementActuator"))}}

    
#### Timing functions 

Timings can be specified explicitly as constant `int` or `float` values (seconds).

!!! example "Example 1"
    ```
    toggle_light(1) @ [10]:*
    ```
    This will toggle light number 1 on/off every 10 seconds.

but we may want some more complicated schedule. This can be acheived using some built-in timing functions to introduce randomness or otherwise.

- `uniform(a : int, b : int)` - a random integer between a and b (inclusive).
- `uniform(a : float, b : float)` - a random float between a and b (inclusive).

!!! example "Example 2"
    ```
    toggle_light(1) @ [uniform(10,20)]:*
    ```
    This will toggle light number 1 on/off at times randomly chosen between 10 and 20 seconds.

We can build more complex schedules that mix timing functions and constant values. 

!!! example "Example 3"
    ```
    toggle_pump_failure("ab") @ [uniform(3,10), 2]:*
    ```
    This will trigger a pump failure for 2 seconds after some random time between 3-10 seconds and repeat.

#### Example Schedules

??? example "Tracking Task Schedule"
    ```
    # this moves the target around randomly by 5 units every 0.1 seconds
    perturb_target(5) @ [0.1]:*
    ```

??? example "System Monitoring Task Schedule"
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

??? example "Resource Management Task Schedule"
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

## Quick Start

Configuration examples can be found [here](https://github.com/dicelab-rhul/matbii/tree/main/matbii/example).

Examples can be run using the `--example` option:

```
python -m matbii --example example-A
```

Events will be logged to `./example-A-logs/`, take a look and make sure everything is working as expected. To start running your own experiments, you can copy the example files, or an [example](https://github.com/dicelab-rhul/matbii/tree/main/matbii/example) and run in the usual way with:

```
python -m matbii -c <CONFIG_PATH>
```
You can set up the logging directory using the `logging.path` option in your [main configuration file](#main-configuration) or by overriding via the command line with `--config.logging.path <PATH>`.

The next page contains details on the logging system and tools for post-experiment analysis/visualisation.
