###  Configuration
- `experiment (ExperimentConfiguration)`: None Defaults to: `None`.
- `participant (ParticipantConfiguration)`: None Defaults to: `None`.
- `guidance (GuidanceConfiguration)`: None Defaults to: `None`.
- `window (WindowConfiguration)`: None Defaults to: `None`.
- `eyetracking (EyetrackingConfiguration)`: None Defaults to: `None`.
- `logging (LoggingConfiguration)`: None Defaults to: `None`.
- `ui (UIConfiguration)`: None Defaults to: `None`.

### Experiment Configuration
- `id (str)`: The unique ID of this experiment. Defaults to: `None`.
- `path (str)`: The full path to the directory containing task configuration files, details on configuring tasks consult the [wiki](https://github.com/dicelab-rhul/matbii/wiki/Task-Configuration). If this is a relative path it is relative to the current working directory. Defaults to: `None`.
- `duration (int)`: The duration (in seconds) of this experiment (the simulation will close after this time), a negative value will leave the simulation running forever. Defaults to: `-1`.
- `enable_video_recording (bool)`: Whether to begin a screen recording of the experiment when the simulation starts, the video will be saved to the logging path when the experiment ends. Defaults to: `False`.
- `enable_tasks (list[str])`: Which tasks to enable at the start of the simulation. Defaults to: `['system_monitoring', 'resource_management', 'tracking']`.
- `meta (dict)`: Any additional meta data you wish to associate with this experiment. Defaults to: `{}`.

### Participant Configuration
- `id (str)`: The unique ID of the participant that is taking part in the experiment. Defaults to: `None`.
- `meta (dict)`: Any additional meta data you wish to associate with the participant. Defaults to: `{}`.

### Guidance Configuration
- `enable (bool)`: Whether to enable guidance, if this is False then no guidance agent will be created. Defaults to: `True`.
- `counter_factual (bool)`: Whether to show guidance to the user, if False then guidance agent will be configured NOT to display guidance but will still take actions for logging purposes (if they support this). Defaults to: `False`.

### Window Configuration
- `x (int)`: None Defaults to: `0`.
- `y (int)`: None Defaults to: `0`.
- `width (int)`: None Defaults to: `640`.
- `height (int)`: None Defaults to: `480`.
- `title (str)`: None Defaults to: `"window"`.
- `resizable (bool)`: None Defaults to: `False`.
- `fullscreen (bool)`: None Defaults to: `False`.
- `background_color (str)`: None Defaults to: `"#ffffff"`.

### Eyetracking Configuration
- `uri (str | None)`: The eyetracker address (example: `'tet-tcp://172.28.195.1'`). For details on setting up eyetracking, consult the [wiki](https://github.com/dicelab-rhul/matbii/wiki/Eyetracking). Defaults to: `None`.
- `sdk (str)`: The eyetracking SDK to use, current options are: ['tobii']. Defaults to: `"tobii"`.
- `enabled (bool)`: Whether eyetracking is enabled. Defaults to: `False`.
- `moving_average_n (int)`: The window size to used to smooth eyetracking coordinates. Defaults to: `5`.
- `velocity_threshold (float)`: The threshold on gaze velocity which will determine saccades/fixations. This is defined in screen space, where the screen coordinates are normalised in the range [0,1]. IMPORTANT NOTE: different monitor sizes may require different values, unfortunately this is difficult to standardise without access to data on the gaze angle (which would be monitor size independent). Defaults to: `0.5`.

### Logging Configuration
- `level (str)`: The logging level to use: ['DEBUG', 'INFO', 'WARNING', 'ERROR'], this will not affect event logging. Defaults to: `"INFO"`.
- `path (str)`: The path to the directory where log files will be written. Defaults to: `"./logs/"`.

### UI Configuration
- `size (tuple[int,int])`: The width and height of the canvas used to render the tasks. This should fully encapsulate all task elements. If a task appears to be off screen, try increasing this value. Defaults to: `(800, 600)`.
- `offset (tuple[int,int])`: The x and y offset used when rendering the root UI element, can be used to pad the top/left of the window. Defaults to: `(0, 0)`.
