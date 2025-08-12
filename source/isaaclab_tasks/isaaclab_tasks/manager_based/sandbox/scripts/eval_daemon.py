import argparse

from isaaclab.app import AppLauncher

# local imports
import cli_args  # isort: skip

# add argparse arguments
parser = argparse.ArgumentParser(description="Train an RL agent with RSL-RL.")
parser.add_argument("--video", action="store_true", default=False, help="Record videos during training.")
parser.add_argument("--video_length", type=int, default=200, help="Length of the recorded video (in steps).")
parser.add_argument(
    "--disable_fabric", action="store_true", default=False, help="Disable fabric and use USD I/O operations."
)
parser.add_argument("--num_envs", type=int, default=None, help="Number of environments to simulate.")
parser.add_argument("--task", type=str, default=None, help="Name of the task.")
parser.add_argument(
    "--use_pretrained_checkpoint",
    action="store_true",
    help="Use the pre-trained checkpoint from Nucleus.",
)
parser.add_argument("--real-time", action="store_true", default=False, help="Run in real-time, if possible.")
# append RSL-RL cli arguments
cli_args.add_rsl_rl_args(parser)
# append AppLauncher cli args
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()
# always enable cameras to record video
if args_cli.video:
    args_cli.enable_cameras = True

# launch omniverse app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import gymnasium as gym
import os
import time
import torch

from rsl_rl.runners import OnPolicyRunner

from isaaclab.envs import DirectMARLEnv, multi_agent_to_single_agent
from isaaclab.utils.assets import retrieve_file_path
from isaaclab.utils.dict import print_dict
from isaaclab.utils.pretrained_checkpoint import get_published_pretrained_checkpoint

from isaaclab_rl.rsl_rl import RslRlOnPolicyRunnerCfg, RslRlVecEnvWrapper, export_policy_as_jit, export_policy_as_onnx

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.utils import get_checkpoint_path, parse_env_cfg

from isaaclab_tasks.manager_based.sandbox.utils import WandbFileWatcher
# from isaaclab.utils import replace_slices_with_strings, replace_strings_with_slices
# from isaaclab.envs.utils.spaces import replace_env_cfg_spaces_with_strings, replace_strings_with_env_cfg_spaces
from omegaconf import OmegaConf
import yaml

# PLACEHOLDER: Extension template (do not remove this comment)


def replace_strings_with_slices(cfg: dict) -> dict:
    for k, v in cfg.items():
        if isinstance(v, dict):
            if v.keys() == {"slice_start", "slice_stop", "slice_step"}:
                cfg[k] = slice(v["slice_start"], v["slice_stop"], v["slice_step"])
            else:
                cfg[k] = replace_strings_with_slices(v)
    return cfg


def main():
    """Play with RSL-RL agent."""

    if args_cli.run_name is None:
        # If only project name specified, use 1st run in project
        path = args_cli.log_project_name
    else:
        # Otherwise, use the run name
        path = f"{args_cli.log_project_name}/{args_cli.run_name}"

    wandb_watcher = WandbFileWatcher(
        path=path, 
        pattern=r".*",
        download_dir="wandb_runs"
    )
    run_dir = os.path.join(wandb_watcher.download_dir, wandb_watcher.run.name)
    
    # Block until files are available
    while not wandb_watcher.update():
        print("Waiting for files to be available...")
        time.sleep(1)

    cfg = OmegaConf.load(os.path.join(run_dir, "config.yaml"))
    loaded_env_cfg = OmegaConf.to_container(cfg.env_cfg.value, resolve=True)

    # loaded_env_cfg = OmegaConf.to_container(cfg.env_cfg.value, resolve=True)
    loaded_env_cfg = replace_strings_with_slices(loaded_env_cfg)
    agent_cfg = cfg["runner_cfg"]["value"]

    task_name = args_cli.task.split(":")[-1]

    # parse configuration
    env_cfg = parse_env_cfg(
        args_cli.task, device=args_cli.device, num_envs=args_cli.num_envs, use_fabric=not args_cli.disable_fabric
    )
    print(f"Env config type: {type(env_cfg)}")
    print(f"{loaded_env_cfg['events']['base_external_force_torque']['func']}")
    env_cfg.from_dict(loaded_env_cfg)

    agent_cfg: RslRlOnPolicyRunnerCfg = cli_args.parse_rsl_rl_cfg(task_name, args_cli)

    # specify directory for logging experiments
    # log_root_path = os.path.join("logs", "rsl_rl", agent_cfg.experiment_name)
    log_root_path = run_dir
    log_root_path = os.path.abspath(log_root_path)
    print(f"[INFO] Loading experiment from directory: {log_root_path}")
    if args_cli.use_pretrained_checkpoint:
        resume_path = get_published_pretrained_checkpoint("rsl_rl", task_name)
        if not resume_path:
            print("[INFO] Unfortunately a pre-trained checkpoint is currently unavailable for this task.")
            return
    elif args_cli.checkpoint:
        resume_path = retrieve_file_path(args_cli.checkpoint)
    else:
        # resume_path = get_checkpoint_path(log_root_path, agent_cfg.load_run, agent_cfg.load_checkpoint)
        resume_path = get_checkpoint_path(log_root_path, run_dir, agent_cfg.load_checkpoint)

    log_dir = os.path.dirname(resume_path)
    # create isaac environment
    env = gym.make(args_cli.task, cfg=env_cfg, render_mode="rgb_array" if args_cli.video else None)

    # convert to single-agent instance if required by the RL algorithm
    if isinstance(env.unwrapped, DirectMARLEnv):
        env = multi_agent_to_single_agent(env)

    # wrap for video recording
    if args_cli.video:
        video_kwargs = {
            "video_folder": os.path.join(log_dir, "videos", "play"),
            "step_trigger": lambda step: step == 0,
            "video_length": args_cli.video_length,
            "disable_logger": True,
        }
        print("[INFO] Recording videos during training.")
        print_dict(video_kwargs, nesting=4)
        if args_cli.logger == "wandb":
            from isaaclab_tasks.manager_based.sandbox.utils import RecordVideo
            env = RecordVideo(env, **video_kwargs)
        else:
            env = gym.wrappers.RecordVideo(env, **video_kwargs)

    # wrap around environment for rsl-rl
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)

    print(f"[INFO]: Loading model checkpoint from: {resume_path}")
    # load previously trained model
    ppo_runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)

    def eval(resume_path: str):
        ppo_runner.load(resume_path)

        # obtain the trained policy for inference
        policy = ppo_runner.get_inference_policy(device=env.unwrapped.device)

        # extract the neural network module
        # we do this in a try-except to maintain backwards compatibility.
        try:
            # version 2.3 onwards
            policy_nn = ppo_runner.alg.policy
        except AttributeError:
            # version 2.2 and below
            policy_nn = ppo_runner.alg.actor_critic

        # export policy to onnx/jit
        export_model_dir = os.path.join(os.path.dirname(resume_path), "exported")
        export_policy_as_jit(policy_nn, ppo_runner.obs_normalizer, path=export_model_dir, filename="policy.pt")
        export_policy_as_onnx(
            policy_nn, normalizer=ppo_runner.obs_normalizer, path=export_model_dir, filename="policy.onnx"
        )

        dt = env.unwrapped.step_dt

        # reset environment
        obs, _ = env.get_observations()
        timestep = 0
        # simulate environment
        while simulation_app.is_running():
            start_time = time.time()
            # run everything in inference mode
            with torch.inference_mode():
                # agent stepping
                actions = policy(obs)
                # env stepping
                obs, _, _, _ = env.step(actions)
            if args_cli.video:
                timestep += 1
                # Exit the play loop after recording one video
                if timestep == args_cli.video_length:
                    break

            # time delay for real-time evaluation
            sleep_time = dt - (time.time() - start_time)
            if args_cli.real_time and sleep_time > 0:
                time.sleep(sleep_time)

        # close the simulator
        env.close()

    while True:        
        new_files = wandb_watcher.update()
        if not new_files:
            time.sleep(30)
            continue
        for file in new_files.values():
            with file.download() as policy_file:
                eval(policy_file.name)



if __name__ == "__main__":
    # run the main function
    main()
    # close sim app
    simulation_app.close()
