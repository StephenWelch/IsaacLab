#!/bin/bash

docker build \
  --build-arg ISAACSIM_BASE_IMAGE_ARG=nvcr.io/nvidia/isaac-lab \
  --build-arg ISAACSIM_VERSION_ARG=2.2.0 \
  --build-arg ISAACSIM_ROOT_PATH_ARG=/isaac-sim \
  --build-arg ISAACLAB_PATH_ARG=/workspace/isaaclab \
  --build-arg DOCKER_USER_HOME_ARG=/root \
  -t isaac-lab-base \
  .