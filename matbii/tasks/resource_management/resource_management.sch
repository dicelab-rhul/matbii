####  Resource Management Task Schedule ####

# these determine pump failures
toggle_pump_failure("fd") @ [uniform(3,10), 2]:*
toggle_pump_failure("fb") @ [uniform(3,10), 2]:*
toggle_pump_failure("db") @ [uniform(3,10), 2]:*
toggle_pump_failure("ec") @ [uniform(3,10), 2]:*
toggle_pump_failure("ea") @ [uniform(3,10), 2]:*
toggle_pump_failure("ca") @ [uniform(3,10), 2]:*
toggle_pump_failure("ba") @ [uniform(3,10), 2]:*
toggle_pump_failure("ab") @ [uniform(3,10), 2]:*

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
