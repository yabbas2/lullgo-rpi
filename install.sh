#!/bin/sh
sudo apt update
sudo apt -y upgrade
sudo apt install -y python3-pip
sudo apt install -y python3-numpy portaudio19-dev libopenblas-dev
sudo apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl git libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
sudo apt install -y python3-gpiozero

curl -fsSL https://pyenv.run | bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init - bash)"' >> ~/.bashrc
exec "$SHELL"

pyenv install 3.9.0
pyenv local 3.9.0

python3 -m venv pyvenv

./pyvenv/bin/pip3 install -r requirements.txt

cd ..
mkdir -p models
MODEL_PATH="./models/yamnet.tflite"
curl -L 'https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/audio_classification/rpi/lite-model_yamnet_classification_tflite_1.tflite' -o ${MODEL_PATH}

sudo npm install -g serve

sudo cp ./services/bcd.service /etc/systemd/system/bcd.service
sudo cp ./services/heartbeat.service /etc/systemd/system/heartbeat.service
sudo cp ./services/parent.service /etc/systemd/system/parent.service
sudo systemctl daemon-reload
sudo systemctl enable bcd.service
sudo systemctl enable heartbeat.service
sudo systemctl enable parent.service

sudo reboot now
