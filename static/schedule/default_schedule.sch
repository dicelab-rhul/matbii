

# TODO schedules that use 0 (or very small values) can cause problems for the browser as the XML update is schedule before the initial sensing of the SVG data. This could be fixed by having the schedule agent wait for the first cycle to finish before starting the schedule...

####  System Monitoring Task Schedule ####

# this makes the lights turn to their unacceptable state "off"
off_light(1) @ [uniform(3,10)]:*    # this means failure for light 1
on_light(2) @ [uniform(3,10)]:*     # this means failure for light 2
# toggle_light(X) is also an option

# this randomly moves the sliders (up/down by 1)
perturb_slider(1) @ [uniform(2,5)]:*
perturb_slider(2) @ [uniform(2,5)]:*
perturb_slider(3) @ [uniform(2,5)]:*
perturb_slider(4) @ [uniform(2,5)]:*

####  Tracking Task Schedule ####

# this moves the target around randomly
perturb_target(5) @ [0.1]:*

####  Resource Management Task Schedule ####

# these determine pump failures
toggle_pump("fd") @ [uniform(3,10), 2]:*
toggle_pump("fb") @ [uniform(3,10), 2]:*
toggle_pump("db") @ [uniform(3,10), 2]:*
toggle_pump("ec") @ [uniform(3,10), 2]:*
toggle_pump("ea") @ [uniform(3,10), 2]:*
toggle_pump("ca") @ [uniform(3,10), 2]:*
toggle_pump("ba") @ [uniform(3,10), 2]:*
toggle_pump("ab") @ [uniform(3,10), 2]:*


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
