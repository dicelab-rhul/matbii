# Eye tracking

Courtesy of [`icua`](https://github.com/dicelab-rhul/icua2), `matbii` supports eye-tracking out of the box. Currently only [tobii pro eye trackers](https://www.tobii.com/) are supported. If you want to make use of another eye tracker provider, see [eye tracker API](#eye-tracker-api).

## Configuration

Eye tracking can be configured via the [main configuration file](configuration.md).

::: matbii.config.EyetrackingConfiguration
    options:
      show_bases: false
      show_labels: true
      inherited_members: true
      members: true
    
    


<!-- 
- `uri (str | None)`: The eye tracker address (example: `'tet-tcp://172.28.195.1'`). If left unspecified `matbii` will attempt to find an eye tracker. Defaults to: `None` (unspecified).
- `sdk (str)`: The eye tracking SDK to use, current options are: `['tobii']`. Defaults to: `'tobii'`.
- `enabled (bool)`: Whether eye tracking is enabled. Defaults to: `False`.
- `moving_average_n (int)`: The window size to used to smooth eyetracking coordinates. Defaults to: `5`.
- `velocity_threshold (float)`: The threshold on gaze velocity which will determine saccades/fixations. This is defined in screen space, where the screen coordinates are normalised in the range [0,1]. **IMPORTANT NOTE:** different monitor sizes may require different values, unfortunately this is difficult to standardise without access to data on the gaze angle (which would be monitor size independent). Defaults to: `0.5`. -->


## Calibration

`matbii` does not currently support calibrating eye trackers as part of the task, this should be done via tools provided by your eyetracker manufacturer. 

### Tobii

Tobii eye trackers can be calibrated using [tobii eye tracker manager](https://connect.tobii.com/s/etm-downloads?). This is also where you will find your eyetracker URI (see [section below](#finding-your-eye-tracker-uri)).


## Finding your eye tracker URI

The URI is used by `matbii` to locate and connect to your eye tracker device. w

### Tobii





TODO take some screen shots!

## Eye tracker API

Like all devices eye trackers are encapsulated in `IOSensor`s. These allow an agent to observe events that come from an IO stream. 

TODO







