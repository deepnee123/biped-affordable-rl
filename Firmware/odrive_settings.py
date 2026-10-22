# tweaked settings for odrive that I found works best
# paste one by one into odrive tool terminal

odrv0.axis0.controller.config.control_mode = CONTROL_MODE_VELOCITY_CONTROL
odrv0.axis0.controller.config.input_mode = 2  # VEL_RAMP
odrv0.save_configuration()
odrv0.reboot()

Position control: 
odrv0.axis0.controller.config.control_mode = CONTROL_MODE_POSITION_CONTROL
odrv0.axis0.controller.config.input_mode = 4  # TRAP_TRAJ
odrv0.save_configuration()
odrv0.reboot()

# Tuning motors, plug these into the custom odrive web interface:
# Parameters: 
# Velocity:
# Vel_gain = 0.1
# Vel_integrator_gain  = 0.1
# Ramp = 100
