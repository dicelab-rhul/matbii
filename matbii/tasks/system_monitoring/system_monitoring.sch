####  System Monitoring Task Schedule ####

# this makes the lights turn to their unacceptable state "off"
off_light(1) @ [1]:*                 # this means failure for light 1
on_light(2) @ [uniform(10,20)]:*     # this means failure for light 2
# toggle_light(X) is also an option

# this randomly moves the sliders (up/down by 1)
perturb_slider(1) @ [uniform(5,6)]:*
perturb_slider(2) @ [uniform(5,6)]:*
perturb_slider(3) @ [uniform(5,6)]:*
perturb_slider(4) @ [uniform(5,6)]:*