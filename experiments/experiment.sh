#!/bin/bash

conda install -c conda-forge -y pinocchio
python scripts/reinforcement_learning/rsl_rl/train.py --headless --wandb-project angmom-loco --logger wandb --task Sandbox-Velocity-Flat-G1-v0 --run_name test