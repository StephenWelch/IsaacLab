FROM nvcr.io/nvidia/isaac-lab:2.2.0

# Build arguments
ARG SSH_PUBLIC_KEY
ARG TS_AUTHKEY
ARG TS_HOSTNAME=isaaclab-container
ARG COMMIT_HASH

# Install dependencies, configure SSH, install Conda, Isaac Lab, and Tailscale in a single layer
RUN set -e \
    # Install system packages
    && apt-get update && apt-get install -y --no-install-recommends \
        openssh-server \
        openssh-client \
        wget \
        bzip2 \
        ca-certificates \
        curl \
        git \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    # Configure SSH
    && mkdir -p /var/run/sshd /root/.ssh \
    && echo 'root:password' | chpasswd \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config \
    && sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config \
    && if [ -n "$SSH_PUBLIC_KEY" ]; then echo "$SSH_PUBLIC_KEY" >> /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys; fi \
    # Install Miniconda
    && wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p /opt/conda \
    && rm /tmp/miniconda.sh \
    && /opt/conda/bin/conda init bash \
    && /opt/conda/bin/conda config --set auto_activate_base false \
    && /opt/conda/bin/conda tos accept --override-channels --channel pkgs/main --channel pkgs/r \
    # Ensure conda is on PATH for subsequent commands in this layer
    && export PATH=/opt/conda/bin:$PATH \
    # Install Isaac Lab environment
    && ./isaaclab.sh -c \
    && source $(conda info --base)/etc/profile.d/conda.sh \
    && conda activate env_isaaclab \
    && ./isaaclab.sh -i rsl_rl\
    && pip install scikit-learn wandb \
    # Install Tailscale
    && curl -fsSL https://tailscale.com/install.sh | sh \
    && mkdir -p /var/lib/tailscale /var/run/tailscale /var/log

# Final environment variables
ENV PATH="/opt/conda/envs/env_isaaclab/bin:/opt/conda/bin:$PATH" \
    CONDA_DEFAULT_ENV=env_isaaclab \
    TS_AUTHKEY=${TS_AUTHKEY} \
    TS_HOSTNAME=${TS_HOSTNAME} \
    COMMIT_HASH=${COMMIT_HASH}

# Expose SSH port
EXPOSE 22

# Setup git repository and prepare experiment script
RUN set -e \
    && cd /workspace \
    && rm -rf isaaclab \
    && git clone https://github.com/StephenWelch/IsaacLab.git isaaclab \
    && cd isaaclab \
    && git checkout $COMMIT_HASH \
    && git submodule update --init --recursive \
    && source $(conda info --base)/etc/profile.d/conda.sh \
    && conda activate env_isaaclab \
    && ./isaaclab.sh -i rsl_rl \
    && chmod +x /workspace/isaaclab/experiments/experiment.sh

COPY startup.sh /usr/local/bin/startup.sh
RUN set -e \
    # Make startup script executable
    && chmod +x /usr/local/bin/startup.sh

# Run startup script on container start
ENTRYPOINT ["/usr/local/bin/startup.sh", "/workspace/isaaclab/experiments/experiment.sh"]