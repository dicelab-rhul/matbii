
Below is a table outlining all configuration options for the resource management task. 
The `cerberus` schema file can be found here.
The `svg` file used to render the task can be found here.

| Field Name         | Type    | Default   | Description |
|--------------------|---------|-----------|-------------|
| x                  | integer | 260       | x position of the task |
| y                  | integer | 360       | y position of the task |
| width              | integer | 540       | width of the task      |
| height             | integer | 300       | height of the task     |
| padding            | integer | 10        | padding surrounding the task               |
| pump_on_color      | color   | "#00ff00" | color of pumps when in the "on" state      |
| pump_off_color     | color   | "#add9e6" | color of pumps when in the "off" state     |
| pump_failure_color | color   | "#ff0000" | color of pumps when in the "failure" state |
| stroke_color       | color   | "#000000" | line colour           |
| stroke_width       | integer | 2         | line width            |
| background_color   | color   | "#ffffff" | background color      |
| debug              | boolean | false     | whether to display debug information               |
| show_tank_labels   | boolean | true      | whether to show textual labels next to each tank   |
| tank_capacity      | dict    |           | See details below:  |
| tank_capacity.a    | integer | 2000      | capacity for tank a |
| tank_capacity.b    | integer | 2000      | capacity for tank b |
| tank_capacity.c    | integer | 1500      | capacity for tank c |
| tank_capacity.d    | integer | 1500      | capacity for tank d |
| tank_capacity.e    | integer | 1000      | capacity for tank e |
| tank_capacity.f    | integer | 1000      | capacity for tank f |
| tank_level         | dict    |           | See details below:                                 |
| tank_level.a       | integer | 1000      | starting fuel level for tank a (< tank_capacity.a) |
| tank_level.b       | integer | 1000      | starting fuel level for tank b (< tank_capacity.b) |
| tank_level.c       | integer | 750       | starting fuel level for tank c (< tank_capacity.c) |
| tank_level.d       | integer | 750       | starting fuel level for tank d (< tank_capacity.d) |
| tank_level.e       | integer | 750       | starting fuel level for tank e (< tank_capacity.e) |
| tank_level.f       | integer | 750       | starting fuel level for tank f (< tank_capacity.f) |
| pump_state         | dict    |           | See details below: |
| pump_state.ab      | str     | off       | starting state of pump ab (options "off", "on", "failure")
| pump_state.ba      | str     | off       | starting state of pump ba (options "off", "on", "failure")
| pump_state.ca      | str     | off       | starting state of pump ca (options "off", "on", "failure")
| pump_state.ec      | str     | off       | starting state of pump ec (options "off", "on", "failure")
| pump_state.ea      | str     | off       | starting state of pump ea (options "off", "on", "failure")
| pump_state.db      | str     | off       | starting state of pump db (options "off", "on", "failure")
| pump_state.fd      | str     | off       | starting state of pump fd (options "off", "on", "failure")
| pump_state.fb      | str     | off       | starting state of pump fb (options "off", "on", "failure")