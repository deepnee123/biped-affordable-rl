import genesis as gs
import numpy as np
import torch

gs.init(backend=gs.amdgpu)

scene = gs.Scene(show_viewer=True)
plane = scene.add_entity(gs.morphs.Plane())

robot = scene.add_entity(
    gs.morphs.MJCF(
        file='my_mjcf/biped_robotv5_patched.xml',
        pos=(0.0, 0.0, 0.6),
    )
)

# IMU sensor — must be added before scene.build()
imu_link = robot.get_link("part_1")  # match your Onshape mate connector name

imu = scene.add_sensor(
    gs.sensors.IMU(
        entity_idx=robot.idx,
        link_idx_local=imu_link.idx_local,
        pos_offset=(0.0, 0.0, 0.0),
        noise=0.01,
        bias=0.0,
        random_walk=0.0,
        draw_debug=True,
    )
)

# create 20 parallel environments
B = 20
scene.build(n_envs=B, env_spacing=(1.0, 1.0))

# all joints (fixed: last entry was "leg4" duplicated, changed to "leg4R")
joints_name = (
    "leg1",
    "leg2",
    "leg3",
    "leg4",
    "leg1R",
    "leg2R",
    "leg3R",
    "leg4R",
)
motors_dof_idx = [robot.get_joint(name).dofs_idx_local[0] for name in joints_name]

# position control
robot.control_dofs_position(
    np.array([-0.5, 0, 0.5, 0.5, 0.5, 0, 0.5, 0.5]),
    motors_dof_idx,
)

# control only specific environments (example, corrected indices):
# robot.control_dofs_position(
#     position=torch.zeros(3, len(motors_dof_idx), device=gs.device),
#     dofs_idx_local=motors_dof_idx,
#     envs_idx=torch.tensor([1, 5, 7], device=gs.device),
# )

# force applied by the controller
print("control force:", robot.get_dofs_control_force(motors_dof_idx))
# actual force experienced by each dof
print("internal force:", robot.get_dofs_force(motors_dof_idx))

# applying external force:
# hand = robot.get_link("insert_side")

# sanity check the IMU read format once before the loop
scene.step()
sample = imu.read()
print(type(sample), sample)

for i in range(1000):
    scene.step()
    imu_data = imu.read()
    # adjust field names once you've seen the printed sample above, e.g.:
    # acc = imu_data.lin_acc
    # gyro = imu_data.ang_vel