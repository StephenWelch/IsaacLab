#!/bin/bash

# Build script for Isaac Lab Docker image with SSH, Miniconda, and Tailscale

# Check if SSH key exists
if [ ! -f ~/.ssh/id_rsa.pub ]; then
    echo "Error: SSH public key not found at ~/.ssh/id_rsa.pub"
    echo "Please generate an SSH key first:"
    echo "  ssh-keygen -t rsa -b 4096"
    exit 1
fi

# Check if TS_AUTHKEY is set
if [ -z "$TS_AUTHKEY" ]; then
    echo "Warning: TS_AUTHKEY environment variable is not set"
    echo "Tailscale will not be authenticated during build"
    echo "To set it, run: export TS_AUTHKEY=your_tailscale_auth_key"
    echo ""
fi

# Read SSH public key content
SSH_PUBLIC_KEY=$(cat ~/.ssh/id_rsa.pub)

# Get current commit hash
COMMIT_HASH=$(git rev-parse HEAD)
echo "Current commit hash: $COMMIT_HASH"

# Build the Docker image with SSH key, TS_AUTHKEY, and commit hash as build arguments
echo "Building Docker image..."
docker build \
    --build-arg SSH_PUBLIC_KEY="$SSH_PUBLIC_KEY" \
    --build-arg TS_AUTHKEY="$TS_AUTHKEY" \
    --build-arg TS_HOSTNAME="isaaclab-container" \
    --build-arg COMMIT_HASH="$COMMIT_HASH" \
    -t isaac-lab-personal .

docker tag isaac-lab-personal ghcr.io/stephenwelch/isaaclab:latest

# Clean up the commit hash file
echo "Cleaning up..."
# rm -f commit_hash.txt

echo "Build complete! You can now run the container with:"
echo "  docker run -d -p 2222:22 --name isaac-ssh isaac-lab-personal"
echo "And connect via SSH with:"
echo "  ssh -p 2222 root@localhost" 