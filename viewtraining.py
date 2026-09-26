import os
import pickle
import argparse
import torch
import genesis as gs
from rsl_rl.runners import OnPolicyRunner
from biped_env import BipedEnv


def find_latest_log_dir(root_dir="logs"):
    if not os.path.isdir(root_dir):
        return None

    runs = []
    for name in os.listdir(root_dir):
        full = os.path.join(root_dir, name)
        if os.path.isdir(full) and os.path.exists(os.path.join(full, "cfgs.pkl")):
            runs.append(full)

    if not runs:
        return None
    return max(runs, key=os.path.getmtime)


def find_latest_checkpoint(log_dir):
    if not os.path.isdir(log_dir):
        return None

    checkpoints = []
    for name in os.listdir(log_dir):
        if name.endswith(".pt") or name.endswith(".pth"):
            checkpoints.append(os.path.join(log_dir, name))

    if not checkpoints:
        return None
    return max(checkpoints, key=os.path.getmtime)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--exp_name", type=str, default="biped_walk")
    parser.add_argument("--checkpoint", type=str, default=None)
    args = parser.parse_args()

    gs.init(backend=gs.amdgpu)

    log_dir = os.path.join("logs", args.exp_name)
    if not os.path.exists(log_dir):
        latest = find_latest_log_dir()
        if latest is None:
            raise FileNotFoundError(
                "No trained logs were found. Train a model first with:\n"
                "  python train_biped.py -e biped_walk -B 30 --max_iterations 6700\n"
                "Then rerun this viewer."
            )
        log_dir = latest
        print(f"[viewtraining] No run named '{args.exp_name}' was found; using latest available log: {log_dir}")

    cfg_path = os.path.join(log_dir, "cfgs.pkl")
    if not os.path.exists(cfg_path):
        raise FileNotFoundError(f"No config file found in {log_dir}. This directory is not a valid trained run.")

    with open(cfg_path, "rb") as f:
        env_cfg, obs_cfg, reward_cfg, command_cfg, train_cfg = pickle.load(f)

    env = BipedEnv(
        num_envs=1,
        env_cfg=env_cfg,
        obs_cfg=obs_cfg,
        reward_cfg=reward_cfg,
        command_cfg=command_cfg,
        show_viewer=True,
        device=gs.device,
    )

    runner = OnPolicyRunner(env, train_cfg, log_dir, device=gs.device.type)

    checkpoint_path = args.checkpoint or find_latest_checkpoint(log_dir)
    if checkpoint_path is not None:
        print(f"[viewtraining] Loading checkpoint: {checkpoint_path}")
        for method_name in ["load", "restore", "resume"]:
            method = getattr(runner, method_name, None)
            if method is not None:
                try:
                    method(checkpoint_path)
                    break
                except TypeError:
                    try:
                        method(path=checkpoint_path)
                        break
                    except TypeError:
                        pass
                except Exception as exc:
                    print(f"[viewtraining] {method_name}({checkpoint_path!r}) failed: {exc}")
                    continue

    policy = runner.get_inference_policy()

    obs, _ = env.reset()
    with torch.no_grad():
        while True:
            actions = policy(obs)
            obs, rewards, dones, infos = env.step(actions)


if __name__ == "__main__":
    main()