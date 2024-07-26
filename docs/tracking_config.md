
Below is a table outlining all configuration options for the tracking task. 

The `cerberus` schema file can be found here.

The `svg` file used to render the task can be found here.

| Field Name        | Type    | Default   | Description |
|-------------------|---------|-----------|-------------|
| x                 | integer | 320       | x position of the task | 
| y                 | integer | 0         | y position of the task | 
| width             | integer | 320       | width of the task      | 
| height            | integer | 320       | height of the task     | 
| padding           | integer | 10        | padding surrounding the task         | 
| debug             | boolean | false     | whether to display debug information |
| line_color        | color   | "#1d90ff" | line color                 |
| target_color      | color   | "#1d90ff" | line color of the target   |
| target_line_width | integer | 4         | width of the target lines            |
| target_x_offset   | integer | 0         | starting x position of the target    |
| target_y_offset   | integer | 0         | starting y position of the target    |
| target_radius     | integer | 25        | size of the target                   |
| dash_array        | string  | "4,2,1,2" | dash array for dashed lines          |