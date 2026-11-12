#!/usr/bin/env bash

source .matspray/bin/activate

export CUDA_HOME=/usr/bin/cuda
export ROOT_DIR=datasets/hesberg_hallway/
export OUTPUT_DIR=output/hesberg/
export OptiX_INSTALL_DIR="$HOME/optix/NVIDIA-OptiX-SDK-9.1.0-linux64-x86_64/"
export SLANG_DIR="$HOME/slang/"
