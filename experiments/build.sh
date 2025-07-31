#!/bin/bash

# Build script for Isaac Lab Docker image with SSH and Miniconda

# Check if SSH key exists
if [ ! -f ~/.ssh/id_rsa.pub ]; then
    echo "Error: SSH public key not found at ~/.ssh/id_rsa.pub"
    echo "Please generate an SSH key first:"
    echo "  ssh-keygen -t rsa -b 4096"
    exit 1
fi

# Copy SSH key to current directory for Docker build
echo "Copying SSH public key from ~/.ssh/id_rsa.pub..."
cp ~/.ssh/id_rsa.pub .

# Write current commit hash to file
# echo "Writing current commit hash to commit_hash.txt..."
# git rev-parse HEAD > commit_hash.txt

# Build the Docker image
echo "Building Docker image..."
docker build -t isaac-lab-personal .

# Clean up the copied SSH key and commit hash file
echo "Cleaning up..."
rm -f id_rsa.pub
# rm -f commit_hash.txt

echo "Build complete! You can now run the container with:"
echo "  docker run -d -p 2222:22 --name isaac-ssh isaac-lab-with-ssh"
echo "And connect via SSH with:"
echo "  ssh -p 2222 root@localhost" 