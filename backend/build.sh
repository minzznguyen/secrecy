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
 
 # Set environment variables to help compiler find PortAudio headers
 export CFLAGS="-I/usr/include/portaudio -I/usr/include"
 export LDFLAGS="-lportaudio"
 
 # Install Python dependencies
 pip install --upgrade pip
 pip install -r requirements.txt