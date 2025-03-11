#!/bin/sh
sudo apt update
sudo apt upgrade -y
sudo apt install python3-pip -y

pip3 install -r requirements.txt
