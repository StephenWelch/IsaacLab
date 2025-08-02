#!/bin/bash
# set -e

# Source conda and activate environment
# source /opt/conda/etc/profile.d/conda.sh
# conda activate env_isaaclab
# export PATH="/opt/conda/envs/env_isaaclab/bin:$PATH"

# Function to start Tailscale
start_tailscale() {
    if [ -n "$TS_AUTHKEY" ]; then
        echo "Starting Tailscale..."
        
        # Create state directory
        mkdir -p /var/lib/tailscale
        
        # Start tailscaled in background with proper logging
        tailscaled --tun=userspace-networking --state=/var/lib/tailscale/tailscaled.state --socket=/var/run/tailscale/tailscaled.sock --verbose=1 > /var/log/tailscaled.log 2>&1 &
        TAILSCALED_PID=$!
        
        # Wait for daemon to be ready
        echo "Waiting for tailscaled to start..."
        sleep 5
        
        # Check if daemon is running
        if ! kill -0 $TAILSCALED_PID 2>/dev/null; then
            echo "Error: tailscaled failed to start"
            cat /var/log/tailscaled.log
            return 1
        fi
        
        echo "tailscaled started with PID: $TAILSCALED_PID"
        
        # Authenticate with Tailscale
        echo "Authenticating with Tailscale..."
        tailscale up --authkey=$TS_AUTHKEY --hostname=$TS_HOSTNAME
        
        if [ $? -eq 0 ]; then
            echo "Tailscale authentication successful"
            tailscale status
        else
            echo "Error: Tailscale authentication failed"
            return 1
        fi
    else
        echo "No TS_AUTHKEY provided, skipping Tailscale"
    fi
}

pull_repo() {
    cd /workspace/isaaclab
    git init
    git remote add origin https://github.com/StephenWelch/IsaacLab.git
    
    # Fetch all branches and commits from remote
    echo "Fetching repository data..."
    git fetch origin
    git reset --hard origin/main
    
    # Check out specific commit if provided
    if [ -n "$COMMIT_HASH" ]; then
        echo "Checking out commit: $COMMIT_HASH"
        if git checkout $COMMIT_HASH; then
            echo "Successfully checked out commit: $COMMIT_HASH"
        else
            echo "Warning: Failed to checkout commit $COMMIT_HASH, falling back to main branch"
            git checkout main
        fi
    else
        echo "No commit hash provided, checking out main branch"
        git checkout main
    fi

    ./isaaclab.sh -i
}

cleanup() {
    echo "Cleaning up"
    tailscale down
    tailscale logout
}

# Start Tailscale
echo "Starting Tailscale"
start_tailscale

echo "Pulling repo"
pull_repo

echo "Starting SSH server"
/usr/sbin/sshd -D &

echo "Trapping SIGTERM"
trap 'cleanup' SIGTERM

# # If a command is provided, run it; otherwise keep container alive
if [ "$#" -gt 0 ]; then
    exec "$@"
else
    echo "Startup tasks finished. Keeping container alive with tail -f /dev/null."
    exec tail -f /dev/null
fi 