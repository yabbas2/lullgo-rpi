#!/bin/sh
sudo apt update
sudo apt -y upgrade
sudo apt install -y python3-pip
sudo apt install -y python3-picamera2 --no-install-recommends
sudo apt install -y python3-libcamera
sudo apt install -y gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly
sudo apt install -y gstreamer1.0-tools gstreamer1.0-alsa alsa-utils gstreamer1.0-pulseaudio
sudo apt install -y python3-numpy portaudio19-dev libopenblas-dev

pip3 install -r requirements.txt

mkdir -p tools
cd tools

wget https://github.com/bluenviron/mediamtx/releases/download/v1.11.3/mediamtx_v1.11.3_linux_armv7.tar.gz
mkdir -p mediamtx
tar -xvzf mediamtx_v1.11.3_linux_armv7.tar.gz -C mediamtx
rm mediamtx_v1.11.3_linux_armv7.tar.gz

git clone https://github.com/HinTak/seeed-voicecard.git
cd seeed-voicecard
git checkout v6.1
sudo ./install.sh

cd ../..
mkdir -p models
MODEL_PATH="./models/yamnet.tflite"
curl -L 'https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/audio_classification/rpi/lite-model_yamnet_classification_tflite_1.tflite' -o ${MODEL_PATH}

sudo reboot now
