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

cd ..
mkdir -p models
MODEL_PATH="./models/yamnet.tflite"
curl -L 'https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/audio_classification/rpi/lite-model_yamnet_classification_tflite_1.tflite' -o ${MODEL_PATH}

sudo cp ./services/pop_remove.service /etc/systemd/system/pop_remove.service
sudo cp ./services/mediamtx.service /etc/systemd/system/mediamtx.service
sudo cp ./services/bcd.service /etc/systemd/system/bcd.service
sudo cp ./services/bcd_server.service /etc/systemd/system/bcd_server.service
sudo cp ./services/ir_server.service /etc/systemd/system/ir_server.service
sudo systemctl daemon-reload
sudo systemctl enable pop_remove.service
sudo systemctl enable mediamtx.service
sudo systemctl enable bcd.service
sudo systemctl enable bcd_server.service
sudo systemctl enable ir_server.service

sudo reboot now
