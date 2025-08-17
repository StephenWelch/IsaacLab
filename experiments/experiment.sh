#!/bin/bash

source $(conda info --base)/etc/profile.d/conda.sh
conda activate env_isaaclab

# Pinocchio/CasADi installation
# conda install -c conda-forge -y pinocchio
# mkdir -p "$CONDA_PREFIX/etc/conda/activate.d"
# printf 'export LD_LIBRARY_PATH="$CONDA_PREFIX/lib:${LD_LIBRARY_PATH}"\n' > "$CONDA_PREFIX/etc/conda/activate.d/000_set_ld_library_path.sh"
# conda deactivate && conda activate env_isaaclab
# pip install --upgrade wandb

# python scripts/reinforcement_learning/rsl_rl/train.py --headless --log_project_name angmom-loco --logger wandb --task Sandbox-Velocity-Flat-G1-v0 --run_name test
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py \
    --headless \
    --log_project_name angmom-loco \
    --logger wandb \
    --task Isaac-Velocity-Flat-G1-v0 \
    --run_name test \
    --headless