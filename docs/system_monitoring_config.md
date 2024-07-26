
Below is a table outlining all configuration options for the system monitoring task. 

The `cerberus` schema file can be found here.

The `svg` file used to render the task can be found here.

| Field Name              | Type    | Default      | Description |
|-------------------------|---------|--------------|-------------|
| x                       | integer | 0            | x position of the task | 
| y                       | integer | 0            | y position of the task | 
| width                   | integer | 240          | width of the task      | 
| height                  | integer | 330          | height of the task     | 
| padding                 | integer | 10           | padding surrounding the task | 
| debug                   | boolean | false        | whether to display debug information  |
| show_keyboard_shortcuts | boolean | false        | whether to display keyboard shortcuts |
| font_size               | integer | 12           | font size   |
| stroke_width            | integer | 2            | line width  |
| light_state             | list    | [0, 0]       | initial states of each light (options: 0 or 1) |
| light_on_color          | color   | "#00ff00"    | color of light 1 when on |
| light_failure_color     | color   | "#ff0000"    | color of light 2 when on |
| light_off_color         | color   | "#add9e6"    | color of light 1 and 2 when off |
| light_width             | integer | 75           | width of each light             |
| light_height            | integer | 50           | height of each light            |
| slider_num_increments   | integer | 11           | number of increments in each slider |
| slider_state            | list    | [5, 5, 5, 5] | intial states of each slider (options: 0 to slider_num_increments-1) |
| slider_width            | integer | 30           | width of each slider            |
| slider_height           | integer | 20           | height of each slider           |
| slider_background_color | color   | "#add9e6"    | slider background color         |
| slider_color            | color   | "#4682b4"    | slider color                    |
| slider_arrow_color      | color   | "#ffff00"    | slider arrow color              |