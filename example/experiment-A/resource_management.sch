####  Resource Management Task Schedule ####

# these determine pump failures, each pump will fail for 3 seconds 
# at some uniformly randomly selected time between 30 and 60 seconds.
toggle_pump_failure("ba") @ [uniform(30,60), 3]:*
toggle_pump_failure("ab") @ [uniform(30,60), 3]:*
toggle_pump_failure("fd") @ [uniform(30,60), 3]:*
toggle_pump_failure("fb") @ [uniform(30,60), 3]:*
toggle_pump_failure("db") @ [uniform(30,60), 3]:*
toggle_pump_failure("ec") @ [uniform(30,60), 3]:*
toggle_pump_failure("ea") @ [uniform(30,60), 3]:*
toggle_pump_failure("ca") @ [uniform(30,60), 3]:*

# these determine the burning of fuel in the two main tanks ("a" and "b")
# 0.5 units will be burned every 0.1 seconds (5 units per second)
burn_fuel("a", 0.5) @ [0.1]:*
burn_fuel("b", 0.5) @ [0.1]:*

# these determine the flow of the pumps, below will transfer 
# 10 units of fuel every 0.1 seconds while the pump is in 
# the "on" state (100 units per second)
pump_fuel("fd", 10) @ [0.1]:*
pump_fuel("fb", 10) @ [0.1]:*
pump_fuel("db", 10) @ [0.1]:*
pump_fuel("ec", 10) @ [0.1]:*
pump_fuel("ea", 10) @ [0.1]:*
pump_fuel("ca", 10) @ [0.1]:*
pump_fuel("ba", 10) @ [0.1]:*
pump_fuel("ab", 10) @ [0.1]:*
