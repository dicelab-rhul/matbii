

# TODO schedules that use 0 (or very small values) can cause problems for the browser 
# as the XML update is schedule before the initial sensing of the SVG data. 
# this could be fixed by having the schedule agent wait for the first cycle to finish before starting the schedule...

#toggle_light(1) @ [10]:*
#perturb_target(5) @ [0.1]:*
burn_fuel("a", 10) @ [0.5]:*


#fail_light(2) @ [uniform(2,5)]:*
#toggle_slider(1) @ [uniform(2,5)]:*
#toggle_slider(2) @ [uniform(2,5)]:*
#toggle_slider(3) @ [uniform(2,5)]:*
#toggle_slider(4) @ [uniform(2,5)]:*