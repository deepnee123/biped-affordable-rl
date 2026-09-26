"""
Biped locomotion env for biped_robotv7.xml.

v7 has pelvis as the true worldbody root with an implicit freejoint --
the left-foot-as-root problem is gone. This means set_pos/set_quat work
correctly, reset logic is straightforward, and all the workarounds from
the v5 file (settling loops, drift correction, action ramps for FK lag)
are no longer needed.

Actuated joints (8): hipRollL, hipYawL, hipPitchL, kneeL,
                     hipRollR, hipYawR, hipPitchR, kneeR
Passive joints (4):  kneePassiveL, parallelLinkBottomL,
                     kneePassiveR, parallelLinkBottomR (equality-constrained)
IMU site: 'imu' on pelvis, pos=(0, -0.00146, 0.0568), identity quat

Reward set: 6 terms from Genesis's official go2_env -- the minimum proven
to produce locomotion. Add terms back one at a time once this trains.
"""

import math
import torch
import genesis as gs

GRAVITY_VEC = torch.tensor([0.0, 0.0, -1.0])


def gs_rand_float(lower, upper, shape, device):
    return (upper - lower) * torch.rand(size=shape, device=device) + lower


def quat_rotate_inverse(q, v):
    q_w   = q[:, 0]
    q_vec = q[:, 1:4]
    a = v * (2.0 * q_w**2 - 1.0).unsqueeze(-1)
    b = torch.cross(q_vec, v, dim=-1) * q_w.unsqueeze(-1) * 2.0
    c = q_vec * torch.sum(q_vec * v, dim=-1, keepdim=True) * 2.0
    return a - b + c


class BipedEnv:
    def __init__(self, num_envs, env_cfg, obs_cfg, reward_cfg, command_cfg,
                 show_viewer=True, device="cuda"):
        self.num_envs = num_envs
        self.device   = torch.device(device)
        self.dt       = env_cfg["dt"]
        self.max_episode_length = int(env_cfg["episode_length_s"] / self.dt)

        self.env_cfg     = env_cfg
        self.obs_cfg     = obs_cfg
        self.reward_cfg  = reward_cfg
        self.command_cfg = command_cfg
        self.reward_scales = dict(reward_cfg["reward_scales"])

        self.num_obs            = obs_cfg["num_obs"]
        self.num_privileged_obs = None
        self.num_actions        = env_cfg["num_actions"]
        self.num_commands       = command_cfg["num_commands"]

        # Per-env grid origins
        num_cols = int(math.ceil(math.sqrt(self.num_envs)))
        spacing  = 2.0
        self.env_origins = torch.zeros((self.num_envs, 3), device=self.device)
        for i in range(self.num_envs):
            self.env_origins[i, 0] = (i % num_cols) * spacing
            self.env_origins[i, 1] = (i // num_cols) * spacing

        # Scene
        self.scene = gs.Scene(
            sim_options=gs.options.SimOptions(dt=self.dt, substeps=2),
            viewer_options=gs.options.ViewerOptions(
                camera_pos=(2.0, 0.0, 1.2),
                camera_lookat=(0.0, 0.0, 0.4),
                camera_fov=40,
            ),
            show_viewer=show_viewer,
        )
        self.scene.add_entity(gs.morphs.Plane())
        self.robot = self.scene.add_entity(
            gs.morphs.MJCF(
                file=env_cfg["mjcf_path"],
                pos=env_cfg["base_init_pos"],
                quat=env_cfg["base_init_quat"],
            )
        )

        self.joint_names    = env_cfg["joint_names"]
        self.motors_dof_idx = [self.robot.get_joint(n).dofs_idx_local[0]
                                for n in self.joint_names]
        # pelvis is now the true root -- get_link works correctly
        self.base_link = self.robot.get_link("pelvis")

        self.scene.build(n_envs=num_envs)

        # Joint config
        self.default_dof_pos = torch.tensor(
            [env_cfg["default_joint_angles"][n] for n in self.joint_names],
            device=self.device, dtype=torch.float32)
        self.dof_pos_lower = torch.tensor(
            [env_cfg["joint_limits"][n][0] for n in self.joint_names],
            device=self.device, dtype=torch.float32)
        self.dof_pos_upper = torch.tensor(
            [env_cfg["joint_limits"][n][1] for n in self.joint_names],
            device=self.device, dtype=torch.float32)

        # Buffers
        N, A, C = self.num_envs, self.num_actions, self.num_commands
        self.obs_buf            = torch.zeros((N, self.num_obs), device=self.device)
        self.rew_buf            = torch.zeros(N,  device=self.device)
        self.reset_buf          = torch.ones(N,   device=self.device, dtype=torch.bool)
        self.episode_length_buf = torch.zeros(N,  device=self.device, dtype=torch.long)
        self.commands           = torch.zeros((N, C), device=self.device)
        self.actions            = torch.zeros((N, A), device=self.device)
        self.last_actions       = torch.zeros((N, A), device=self.device)
        self.dof_pos            = torch.zeros((N, A), device=self.device)
        self.dof_vel            = torch.zeros((N, A), device=self.device)
        self.base_lin_vel       = torch.zeros((N, 3), device=self.device)
        self.base_ang_vel       = torch.zeros((N, 3), device=self.device)
        self.projected_gravity  = torch.zeros((N, 3), device=self.device)
        self.base_pos           = torch.zeros((N, 3), device=self.device)
        self.base_quat          = torch.zeros((N, 4), device=self.device)
        self.extras             = {"observations": {}}

        # Foot contact tracking for air-time reward
        self.left_foot_link  = self.robot.get_link(env_cfg["left_foot_link"])
        self.right_foot_link = self.robot.get_link(env_cfg["right_foot_link"])
        self.foot_air_time   = torch.zeros((N, 2), device=self.device)
        self.last_contacts   = torch.zeros((N, 2), device=self.device, dtype=torch.bool)
        self.contact_height_threshold = env_cfg.get("contact_height_threshold", 0.04)
        self.foot_z          = torch.zeros((N, 2), device=self.device)

        self.target_base_height = None

        # Reward setup
        self.reward_functions = {}
        self.episode_sums     = {}
        for name in list(self.reward_scales.keys()):
            self.reward_scales[name] *= self.dt
            self.reward_functions[name] = getattr(self, "_reward_" + name)
            self.episode_sums[name]     = torch.zeros(N, device=self.device)

        self.reset_idx(torch.arange(N, device=self.device))

        # Measure actual post-reset pelvis height as the height target
        self.target_base_height = self.base_pos[:, 2].mean().item()
        print(f"[BipedEnv] target_base_height:  {self.target_base_height:.3f} m")
        print(f"[BipedEnv] projected_gravity[0]: {self.projected_gravity[0].tolist()}")

        # Forward-axis diagnostic: rotate world-X and world-Y into the pelvis
        # local frame to see which one corresponds to "forward" for this robot.
        # The axis with the larger component in the pelvis local frame is forward.
        world_x = torch.tensor([[1.,0.,0.]], device=self.device).expand(self.num_envs,-1)
        world_y = torch.tensor([[0.,1.,0.]], device=self.device).expand(self.num_envs,-1)
        local_x = quat_rotate_inverse(self.base_quat, world_x)
        local_y = quat_rotate_inverse(self.base_quat, world_y)
        print(f"[BipedEnv] world-X in pelvis frame: {local_x[0].tolist()}")
        print(f"[BipedEnv] world-Y in pelvis frame: {local_y[0].tolist()}")
        print(f"[BipedEnv] base_lin_vel[:, 0] = local X velocity (commands[:,0] tracks this)")
        print(f"[BipedEnv] base_lin_vel[:, 1] = local Y velocity (commands[:,1] tracks this)")
        print(f"[BipedEnv] If robot walks sideways, swap lin_vel_x_range and lin_vel_y_range")
        print(f"[BipedEnv] OR flip the tracking reward to use base_lin_vel[:,1] for forward.")

        if abs(self.projected_gravity[0, 2].item() + 1.0) > 0.15:
            print("[BipedEnv] WARNING: gravity z not close to -1 -- "
                  "check base_init_quat, robot may not be spawning upright.")

    # ------------------------------------------------------------------
    def _resample_commands(self, envs_idx):
        self.commands[envs_idx, 0] = gs_rand_float(
            *self.command_cfg["lin_vel_x_range"], (len(envs_idx),), self.device)
        self.commands[envs_idx, 1] = gs_rand_float(
            *self.command_cfg["lin_vel_y_range"], (len(envs_idx),), self.device)
        self.commands[envs_idx, 2] = gs_rand_float(
            *self.command_cfg["ang_vel_range"],   (len(envs_idx),), self.device)

    def _update_state(self):
        self.dof_pos      = self.robot.get_dofs_position(self.motors_dof_idx)
        self.dof_vel      = self.robot.get_dofs_velocity(self.motors_dof_idx)
        self.base_quat    = self.base_link.get_quat()
        self.base_pos     = self.base_link.get_pos()
        g = GRAVITY_VEC.to(self.device).unsqueeze(0).expand(self.num_envs, -1)
        self.base_lin_vel    = quat_rotate_inverse(self.base_quat, self.base_link.get_vel())
        self.base_ang_vel    = quat_rotate_inverse(self.base_quat, self.base_link.get_ang())
        self.projected_gravity = quat_rotate_inverse(self.base_quat, g)

        lf_pos = self.left_foot_link.get_pos()
        rf_pos = self.right_foot_link.get_pos()
        self.foot_z = torch.stack([lf_pos[:, 2], rf_pos[:, 2]], dim=1)

    def _compute_obs(self):
        # 33 = ang_vel(3) + proj_gravity(3) + commands(3) + dof_pos(8) + dof_vel(8) + last_actions(8)
        self.obs_buf = torch.cat([
            self.base_ang_vel    * self.obs_cfg["obs_scales"]["ang_vel"],
            self.projected_gravity,
            self.commands        * self.obs_cfg["obs_scales"]["commands"],
            (self.dof_pos - self.default_dof_pos) * self.obs_cfg["obs_scales"]["dof_pos"],
            self.dof_vel         * self.obs_cfg["obs_scales"]["dof_vel"],
            self.last_actions,
        ], dim=-1)

    # ------------------------------------------------------------------
    def step(self, actions):
        self.actions = torch.clip(
            actions, -self.env_cfg["clip_actions"], self.env_cfg["clip_actions"])

        # One-step action latency (matches go2_env)
        exec_actions = (self.last_actions
                        if self.env_cfg.get("simulate_action_latency", True)
                        else self.actions)
        target = self.default_dof_pos + exec_actions * self.env_cfg["action_scale"]
        target = torch.clip(target, self.dof_pos_lower, self.dof_pos_upper)
        self.robot.control_dofs_position(target, self.motors_dof_idx)

        self.scene.step()
        self.episode_length_buf += 1
        self._update_state()

        # Termination: roll/pitch past threshold (go2_env style)
        roll_deg  = torch.abs(
            torch.arcsin(torch.clamp(self.projected_gravity[:, 1], -1.0, 1.0))) * 57.3
        pitch_deg = torch.abs(
            torch.arcsin(torch.clamp(self.projected_gravity[:, 0], -1.0, 1.0))) * 57.3
        timed_out = self.episode_length_buf >= self.max_episode_length
        fallen    = ((roll_deg  > self.env_cfg["termination_if_roll_greater_than"]) |
                     (pitch_deg > self.env_cfg["termination_if_pitch_greater_than"]))
        self.reset_buf = fallen | timed_out

        # Rewards
        self.rew_buf[:] = 0.0
        for name, func in self.reward_functions.items():
            r = func() * self.reward_scales[name]
            self.rew_buf += r
            self.episode_sums[name] += r

        self.last_actions[:] = self.actions

        # Update foot air-time tracking
        contacts = self.foot_z < self.contact_height_threshold
        self.foot_air_time += self.dt
        self.foot_air_time[contacts] = 0.0
        self.last_contacts = contacts

        # Logging & resets
        reset_idx = self.reset_buf.nonzero(as_tuple=False).flatten()
        self.extras["episode"] = {}
        if len(reset_idx) > 0:
            for key in self.episode_sums:
                self.extras["episode"][key] = torch.mean(
                    self.episode_sums[key][reset_idx])
            self.reset_idx(reset_idx)
            self._update_state()

        self._compute_obs()

        resample_idx = (
            self.episode_length_buf %
            int(self.command_cfg["resample_time_s"] / self.dt) == 0
        ).nonzero(as_tuple=False).flatten()
        if len(resample_idx) > 0:
            self._resample_commands(resample_idx)

        return self.obs_buf, self.rew_buf, self.reset_buf, self.extras

    # ------------------------------------------------------------------
    def reset_idx(self, envs_idx):
        if len(envs_idx) == 0:
            return

        # Joint angles with small noise
        noise   = gs_rand_float(-0.05, 0.05, (len(envs_idx), self.num_actions), self.device)
        dof_pos = torch.clip(self.default_dof_pos + noise,
                             self.dof_pos_lower, self.dof_pos_upper)
        self.robot.set_dofs_position(dof_pos, self.motors_dof_idx, envs_idx=envs_idx)

        # Pelvis is the root -- set_pos/set_quat directly moves the pelvis
        base_pos = self.env_origins[envs_idx] + torch.tensor(
            self.env_cfg["base_init_pos"], device=self.device)
        base_quat = torch.tensor(
            self.env_cfg["base_init_quat"], device=self.device
        ).unsqueeze(0).expand(len(envs_idx), -1)
        self.robot.set_pos(base_pos,   envs_idx=envs_idx)
        self.robot.set_quat(base_quat, envs_idx=envs_idx)
        self.robot.zero_all_dofs_velocity(envs_idx=envs_idx)

        self.last_actions[envs_idx]       = 0.0
        self.foot_air_time[envs_idx]      = 0.0
        self.last_contacts[envs_idx]      = False
        self.episode_length_buf[envs_idx]  = 0
        self._resample_commands(envs_idx)
        self._update_state()

        for key in self.episode_sums:
            self.episode_sums[key][envs_idx] = 0.0

    def reset(self):
        self.reset_idx(torch.arange(self.num_envs, device=self.device))
        self._update_state()
        self._compute_obs()
        return self.obs_buf, self.extras

    def get_observations(self):
        return self.obs_buf, self.extras

    # ------------------------------------------------------------------
    # Reward terms -- 6 terms from Genesis go2_env
    # ------------------------------------------------------------------
    def _reward_tracking_lin_vel(self):
        # commands[:, 0] = target forward speed, commands[:, 1] = target lateral speed
        # forward_axis / lateral_axis set in env_cfg -- see startup diagnostic print.
        # If robot walks sideways, set forward_axis=1, lateral_axis=0 in env_cfg.
        fwd = self.env_cfg.get("forward_axis", 0)
        lat = self.env_cfg.get("lateral_axis", 1)
        err = (torch.square(self.commands[:, 0] - self.base_lin_vel[:, fwd]) +
               torch.square(self.commands[:, 1] - self.base_lin_vel[:, lat]))
        return torch.exp(-err / self.reward_cfg["tracking_sigma"])

    def _reward_tracking_ang_vel(self):
        err = torch.square(self.commands[:, 2] - self.base_ang_vel[:, 2])
        return torch.exp(-err / self.reward_cfg["tracking_sigma"])

    def _reward_lin_vel_z(self):
        return torch.square(self.base_lin_vel[:, 2])

    def _reward_action_rate(self):
        return torch.sum(torch.square(self.last_actions - self.actions), dim=1)

    def _reward_base_height(self):
        if self.target_base_height is None:
            return torch.zeros(self.num_envs, device=self.device)
        return torch.square(self.base_pos[:, 2] - self.target_base_height)

    def _reward_similar_to_default(self):
        return torch.sum(torch.abs(self.dof_pos - self.default_dof_pos), dim=1)

    def _reward_foot_air_time(self):
        """
        Reward feet for staying in the air long enough to constitute a real
        stride. Without this the policy learns fast tiny shuffling steps which
        are a local optimum for velocity tracking but don't transfer well to
        real hardware (high frequency, low clearance, hard to actuate cleanly).

        Gives a one-shot bonus at each foot touchdown proportional to how long
        that foot was airborne, minus a minimum threshold. Only fires when the
        robot is actually commanded to move.
        """
        min_air_time = self.reward_cfg.get("min_air_time", 0.2)
        # just_landed: in contact now, wasn't last step
        in_contact_now  = self.foot_z < self.contact_height_threshold
        just_landed = in_contact_now & ~self.last_contacts
        air_time_bonus  = torch.clamp(self.foot_air_time - min_air_time, min=-0.5, max=0.5)
        # only reward when commanded to move, not when standing still
        moving = (torch.norm(self.commands[:, :2], dim=1) > 0.1).float().unsqueeze(1)
        return torch.sum(air_time_bonus * just_landed.float() * moving, dim=1)