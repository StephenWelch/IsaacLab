wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

git remote add origin <my repo>
git reset --hard origin/main
git checkout <my branch>
./isaaclab.sh -c
./isaaclab.sh -i
conda install pinocchio -c conda-forge
python scripts/reinforcement_learning/rsl_rl/train.py --task Sandbox-Velocity-Flat-G1-v0 --video --log_project_name cusadi_loco --logger wandb --run_name angmom-rew__gamma-0_10 --video