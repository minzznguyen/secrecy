#!/bin/bash

# Install system dependencies
apt-get update && apt-get install -y \
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