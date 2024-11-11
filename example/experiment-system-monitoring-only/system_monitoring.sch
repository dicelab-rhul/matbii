####  System Monitoring Task Schedule ####

# this makes the lights turn to their unacceptable state "off"
off_light(1) @ [5]:*    # this means failure for light 1
on_light(2) @ [5]:*     # this means failure for light 2

# this randomly moves the sliders (up/down by 1)
perturb_slider(1) @ [5]:*
perturb_slider(2) @ [5]:*
perturb_slider(3) @ [5]:*
perturb_slider(4) @ [5]:*