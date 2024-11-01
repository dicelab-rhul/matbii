
## Parsing Event Log Files

TODO acceptaility intervals should contain relevant state information about the task? this would be useful...

### Acceptability

- Acceptability intervals: A dataframe of intervals (t1, t2, task) that indicate the time at which a task was in an unacceptable state. At times inbetween intervals, the task is in an acceptable state.

- Guidance intervals: A dataframe of intervals (t1, t2, task) that indicate the time at which a guidance was shown.At times inbetween intervals, no guidance was shown.

### User input 

- Mouse movement events: A dataframe of mouse movements (t, x, y).
- Mouse click events: A dataframe of mouse click events (t, x, y, b). b indicates which button was clicked.
- Keyboard events: A dataframe of keyboard events (t, key).
- Eye movement events: A dataframe of eye tracking events (t, x, y, f). f indicates whether the event part of a fixation or saccade. Note that the (x, y) coordinates already have been passed through filters.

### Task specific 

- Tracking: A dataframe of tracking events (t, x, y) showing the position of the tracking target.
- System monitoring: A dataframe of system monitoring events (t, *lights, *sliders).
- Fuel monitoring: A dataframe of fuel monitoring events (t, *tanks, *pumps).





## Testing Eye tracking parameters

There is a script at `matbii\scripts\visualise_eyetracking\visualise_eyetracking.py` which visualises eyetracking.

To run it:

1. Active the dev envirnonment
```conda activate matbii-dev```

2. make sure you're in the correct directory (.../matbii/scripts/visualise_eyetracking)
```cd visualise_eyetracking```

3. Check what parameters you can give the script:
```python visualise_eyetracking.py --help```

4. Run the script, e.g:
```python visualise_eyetracking.py --uri tet-tcp://169.254.126.68```

Obviously make sure the eyetracker is on and calibrated in the eyetracker manager!

The eyetracking position is represented as a blue dot, the mouse position is a red dot. 
The blue dot will change its size depending on fixation/saccade. Small for fixation, large for saccade.
You can test different eyetracking filter parameters to get an idea of what will work well for an experiment.

IMPORTANT: as of matbii version 0.0.8 the moving average filter works on no. events rather than time, this means that you will get different results for different sampling rates (e.g. 60hz vs 300hz). Make a note of the sampling rate when you select these parameters! the sampling rate is usually listed (and sometimes configurable) in your eye tracker manager software.

There are plans to update the filter behaviour to use time instead of no. events for consistency, so check this in the latest version notes (if the `moving_avg_n` parameter is deprecated, then you know).

If the eyetracker fails to load you will get a message in the console saying so (its probably a URI issue, make sure you get it from your eyetracker manager and the eyetracker has been calibrated and is on).
