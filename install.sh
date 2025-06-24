#!/bin/sh
sudo apt update
sudo apt -y upgrade
sudo apt install -y python3-pip
sudo apt install -y python3-picamera2 --no-install-recommends
sudo apt install -y python3-libcamera
sudo apt install -y gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly
sudo apt install -y gstreamer1.0-tools gstreamer1.0-alsa alsa-utils gstreamer1.0-pulseaudio
sudo apt install -y python3-numpy portaudio19-dev libopenblas-dev
sudo apt install -y python3-flask

pip3 install -r requirements.txt

mkdir -p tools
cd tools

wget https://github.com/bluenviron/mediamtx/releases/download/v1.11.3/mediamtx_v1.11.3_linux_armv7.tar.gz
mkdir -p mediamtx
tar -xvzf mediamtx_v1.11.3_linux_armv7.tar.gz -C mediamtx
rm mediamtx_v1.11.3_linux_armv7.tar.gz

wget https://nodejs.org/dist/v22.16.0/node-v22.16.0-linux-armv7l.tar.gz
tar -xvf node-v22.16.0-linux-armv7l.tar.gz
sudo cp -r node-v22.16.0-linux-armv7l/ /etc/node-v22.16.0/
sudo ln -s /etc/node-v22.16.0/bin/node /usr/bin/node
sudo ln -s /etc/node-v22.16.0/bin/npm /usr/bin/npm
rm -rf node-v22.16.0-linux-armv7l/
rm node-v22.16.0-linux-armv7l.tar.gz

cd ..
mkdir -p models
MODEL_PATH="./models/yamnet.tflite"
curl -L 'https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/audio_classification/rpi/lite-model_yamnet_classification_tflite_1.tflite' -o ${MODEL_PATH}

sudo npm install -g serve

sudo cp ./services/pop_remove.service /etc/systemd/system/pop_remove.service
sudo cp ./services/mediamtx.service /etc/systemd/system/mediamtx.service
sudo cp ./services/bcd.service /etc/systemd/system/bcd.service
sudo cp ./services/bcd_server.service /etc/systemd/system/bcd_server.service
sudo cp ./services/ir_server.service /etc/systemd/system/ir_server.service
sudo cp ./services/pwa_server.service /etc/systemd/system/pwa_server.service
sudo systemctl daemon-reload
sudo systemctl enable pop_remove.service
sudo systemctl enable mediamtx.service
sudo systemctl enable bcd.service
sudo systemctl enable bcd_server.service
sudo systemctl enable ir_server.service
sudo systemctl enable pwa_server.service

sudo reboot now
