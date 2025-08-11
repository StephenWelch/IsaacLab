#!/bin/bash

source $(conda info --base)/etc/profile.d/conda.sh
conda activate env_isaaclab
conda install -c conda-forge -y pinocchio
python scripts/reinforcement_learning/rsl_rl/train.py --headless --log-project-name angmom-loco --logger wandb --task Sandbox-Velocity-Flat-G1-v0 --run_name test