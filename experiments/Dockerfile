# FROM nvcr.io/nvidia/isaac-lab:2.2.0
FROM isaac-lab-base

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
    # Install Tailscale
    && curl -fsSL https://tailscale.com/install.sh | sh \
    # Clone personal repo
    && mkdir -p /var/lib/tailscale /var/run/tailscale /var/log \
    && cd /workspace \
    && rm -rf isaaclab \
    && git clone https://github.com/StephenWelch/IsaacLab.git isaaclab \
    && ln -s /isaac-sim isaaclab/_isaac_sim

# Build arguments
ARG SSH_PUBLIC_KEY
ARG TS_HOSTNAME=isaaclab-container
ARG COMMIT_HASH

# Final environment variables
ENV CONDA_DEFAULT_ENV=env_isaaclab \
    TS_HOSTNAME=${TS_HOSTNAME} \
    COMMIT_HASH=${COMMIT_HASH} \
    ACCEPT_EULA=Y

# Expose SSH port
EXPOSE 22

COPY startup.sh /usr/local/bin/startup.sh

# Setup git repository and prepare experiment script
RUN set -e \
    && cd /workspace/isaaclab \
    && git fetch origin \
    && git checkout $COMMIT_HASH \
    && git submodule update --init --recursive \
    && source $(conda info --base)/etc/profile.d/conda.sh && conda activate env_isaaclab \
    && ./isaaclab.sh -i rsl_rl \
    && chmod +x /workspace/isaaclab/experiments/experiment.sh \
    && chmod +x /usr/local/bin/startup.sh


# Run startup script on container start
ENTRYPOINT ["/usr/local/bin/startup.sh", "/workspace/isaaclab/experiments/experiment.sh"]