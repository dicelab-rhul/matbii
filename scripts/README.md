
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

IMPORTANT: as of matbii version 0.0.8 the moving average filter works on events rather than time, this means that you will get different results for different sampling rates (e.g. 60hz vs 300hz). Make a note of the sampling rate when you select these parameters! the sampling rate is usually listed (and sometimes configurable) in your eye tracker manager software.

There are plans to update the filter behaviour for consistency, so check this in the latest version notes (if the moving_avg_n parameter is deprecated, then you know).

If the eyetracker fails to load you will get a message in the console saying so (its probably a URI issue, make sure you get it from your eyetracker manager and the eyetracker has been calibrated and is on).
