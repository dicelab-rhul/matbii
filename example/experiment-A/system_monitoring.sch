####  System Monitoring Task Schedule ####

# this toggles lights between their states ("on" -> "off" or "off" -> "on")
# will happen at a repeating uniformly random time between 30 and 60 seconds
toggle_light(1) @ [uniform(30,60)]:* 
toggle_light(2) @ [uniform(30,60)]:* 

# this randomly moves the sliders (up/down by 1)
# will happen at a repeating uniformly random time between 30 and 60 seconds
perturb_slider(1) @ [uniform(30,60)]:*
perturb_slider(2) @ [uniform(30,60)]:*
perturb_slider(3) @ [uniform(30,60)]:*
perturb_slider(4) @ [uniform(30,60)]:*


# vvvv COMMENTED OUT vvvv but could be used...
# off_light(1) @ [uniform(10,20)]:*  # this means failure for light 1
# on_light(2)  @ [uniform(10,20)]:*  # this means failure for light 2
