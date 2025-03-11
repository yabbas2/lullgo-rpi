#!/bin/sh
sudo apt update
sudo apt -y upgrade
sudo apt install -y python3-pip
sudo apt install -y python3-picamera2 --no-install-recommends
sudo apt install -y python3-libcamera

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
sudo reboot now
