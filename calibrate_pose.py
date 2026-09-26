"""
Run this FIRST, before touching the RL env.

The robot's <freejoint> lives on `insert_side_lower_leg` (the LEFT FOOT
assembly) rather than a pelvis/torso, because that's how the Onshape export
picked its root link. That means when we "place the base" for a reset, we're
actually placing the origin of the left foot in space -- not the pelvis.

This script drops the robot with a candidate default pose and prints out
where the pelvis ("part_1") and both feet actually end up, so you can pick a
good `base_init_pos` / `default_joint_angles` for the real training env
instead of guessing blind.

Usage:
    python calibrate_pose.py
Then watch the viewer and read the printed numbers. Adjust BASE_INIT_POS
and/or DEFAULT_JOINT_ANGLES below and re-run until:
  - the pelvis height looks like a sane standing/crouching height
  - neither foot is clipped into the ground on spawn
  - the robot doesn't immediately faceplant on drop (a LITTLE settling motion
    is fine -- that's why we run 200 steps and print at the end)
"""

import numpy as np
import genesis as gs

gs.init(backend=gs.amdgpu)

# ---- candidates to tune -----------------------------------------------
BASE_INIT_POS = (0.0, 0.0, 0.45)          # position of the LEFT FOOT origin at reset
BASE_INIT_QUAT = (-1.0, 0.0, 0.0, 0.0)    # identity orientation for the foot body

JOINT_NAMES = ["leg1", "leg2", "leg3", "leg4", "leg1R", "leg2R", "leg3R", "leg4R"]

# midpoints of each joint's <range> from the MJCF -- a reasonable neutral
# crouch to start from; the RL policy will refine this through training
DEFAULT_JOINT_ANGLES = {
    "leg1": -0.5236, "leg2": -0.0091, "leg3": 1, "leg4": 0.14,
    "leg1R": 0.5236, "leg2R": -0.0063, "leg3R": -1, "leg4R": -0.14,
}
# -------------------------------------------------------------------------

scene = gs.Scene(show_viewer=True)
scene.add_entity(gs.morphs.Plane())

robot = scene.add_entity(
    gs.morphs.MJCF(
        file="my_mjcf/biped_robotv5_patched.xml",
        pos=BASE_INIT_POS,
        quat=BASE_INIT_QUAT,
    )
)

scene.build(n_envs=1)

motors_dof_idx = [robot.get_joint(name).dofs_idx_local[0] for name in JOINT_NAMES]
default_pos = np.array([DEFAULT_JOINT_ANGLES[name] for name in JOINT_NAMES])

robot.set_dofs_position(default_pos, motors_dof_idx)

pelvis = robot.get_link("part_1")
left_foot = robot.get_link("insert_side_lower_leg")
right_foot = robot.get_link("foot_mirrored")

for i in range(1000):
    robot.control_dofs_position(default_pos, motors_dof_idx)
    scene.step()

    if i % 20 == 0:
        p_pos = pelvis.get_pos()
        lf_pos = left_foot.get_pos()
        rf_pos = right_foot.get_pos()
        print(
            f"step {i:3d} | pelvis z={p_pos[0, 2].item():.3f} | "
            f"left foot z={lf_pos[0, 2].item():.3f} | right foot z={rf_pos[0, 2].item():.3f}"
        )

print("\nFinal state after settling:")
print("pelvis pos:", pelvis.get_pos())
print("pelvis quat:", pelvis.get_quat())
print("left foot pos:", left_foot.get_pos())
print("right foot pos:", right_foot.get_pos())
print(
    "\nIf the feet z-values are near 0 and the pelvis didn't tip over, "
    "these BASE_INIT_POS / DEFAULT_JOINT_ANGLES values are a reasonable "
    "starting point for env_cfg in biped_env.py."
)
