FROM nvcr.io/nvidia/isaac-lab:2.1.0

SHELL ["/bin/bash", "-c"]

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openssh-server \
    openssh-client \
    wget \
    bzip2 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p /opt/conda \
    && rm /tmp/miniconda.sh

# Create SSH directory and configure SSH server
RUN mkdir -p /var/run/sshd \
    && echo 'root:password' | chpasswd \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Create .ssh directory for root user
RUN mkdir -p /root/.ssh \
    && chmod 700 /root/.ssh

# Copy SSH public key (will be provided during build)
COPY id_rsa.pub /tmp/id_rsa.pub
RUN cat /tmp/id_rsa.pub >> /root/.ssh/authorized_keys \
    && chmod 600 /root/.ssh/authorized_keys \
    && rm /tmp/id_rsa.pub

# Add conda to PATH and accept terms of service
ENV PATH="/opt/conda/bin:$PATH"
RUN conda init bash \
    && conda config --set auto_activate_base false \
    && conda tos accept --override-channels --channel pkgs/main --channel pkgs/r \
    && ./isaaclab.sh -c

SHELL ["conda", "run", "-n", "env_isaaclab", "/bin/bash", "-c"]


# Expose SSH port
EXPOSE 22

# Start SSH service
CMD ["/usr/sbin/sshd", "-D"]