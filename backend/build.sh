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
     libavcodec-dev
 
 # Install Python dependencies
 pip install --upgrade pip
 pip install -r requirements.txt 