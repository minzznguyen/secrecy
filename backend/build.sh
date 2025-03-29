#!/bin/bash

# Make sure the script is executable
chmod +x build.sh

# Install system dependencies
sudo apt-get update && sudo apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    gcc \
    python3-dev \
    ffmpeg \
    libavcodec-extra \
    libavformat-dev \
    libavutil-dev \
    libavdevice-dev \
    libavfilter-dev \
    libswscale-dev \
    libavresample-dev \
    libavcodec-dev \
    libportaudio-dev

# Install Python dependencies
pip install --upgrade pip

# Install pyaudio with specific version that's known to work
pip install pyaudio==0.2.13

# Install other requirements
pip install -r requirements.txt 