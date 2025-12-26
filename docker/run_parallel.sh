#!/bin/bash
set -e

# Path to your repo root
REPO_ROOT=$(pwd)
IMAGE_NAME="ouroboros-optimizer"
NETWORK_NAME="ouroboros-net"

# build image
echo "Building Docker image..."
docker build -t $IMAGE_NAME -f docker/Dockerfile .

# Create a network if it doesn't exist (optional, mostly for cleanliness)
docker network create $NETWORK_NAME 2>/dev/null || true

# Check for credentials (optional, adjust based on actual auth method)
# Assuming local gcloud config for simplicity in this example
GCLOUD_CONFIG="$HOME/.config/gcloud"

# Configuration
TARGET_SKILLS="${SKILLS:-}"
TARGET_STORIES="${STORIES:-stories/optimization/*.story.md}"

echo "Starting parallel optimization runs..."
echo "Target Stories: $TARGET_STORIES"

# Loop through skills and launch a container for each
for skill_dir in skills/*; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")
        
        # Filter skills if SKILLS env var is set
        if [ -n "$TARGET_SKILLS" ]; then
            if [[ ",$TARGET_SKILLS," != *",$skill_name,"* ]]; then
                continue
            fi
        fi

        echo "Launching optimization for skill: $skill_name"
        
        # Container name must be unique
        container_name="opt-$skill_name-$(date +%s)"
        
        # Launch in detached mode
        # Mounts:
        # 1. Repo root -> /app
        # 2. Host gcloud config -> /root/.config/gcloud (Standard GCP auth)
        # 3. Host configstore -> /root/.config/configstore (Node.js CLI auth)
        docker run -d \
            --name "$container_name" \
            --network "$NETWORK_NAME" \
            -v "$REPO_ROOT:/app" \
            -v "$HOME/.config/gcloud:/root/.config/gcloud" \
            -v "$HOME/.config/configstore:/root/.config/configstore" \
            -v "/usr/bin/gemini:/usr/bin/gemini" \
            -e GEMINI_MODEL="gemini-3-flash-preview" \
            $IMAGE_NAME \
            --trainset "$TARGET_STORIES" \
            --skill "$skill_name" \
            --gemini-binary "/usr/bin/gemini" \
            --max-rollouts 5
            
        echo "Started container: $container_name"
    fi
done

echo "All jobs submitted. Use 'docker ps' to monitor."
