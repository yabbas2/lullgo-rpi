import subprocess
import time
import logging
import re

# configure logging
logging.basicConfig(level=logging.INFO)

NETWORK_UP_DELAY = 2  # in seconds
NETWORK_SCAN_INTERVAL = 5  # in seconds
NETWORK_CONNECT_DELAY = 5  # in seconds


async def enable_network() -> bool:
    try:
        subprocess.run("sudo nmcli radio wifi on", check=True, shell=True)
        time.sleep(NETWORK_UP_DELAY)
        return True
    except subprocess.CalledProcessError as e:
        logging.info(f"Error enabling wifi: {e}")
        return False


async def scan_network() -> list | None:
    try:
        subprocess.run("sudo nmcli dev wifi rescan", check=True, shell=True)
        time.sleep(NETWORK_SCAN_INTERVAL)
        result = subprocess.run("sudo nmcli --get-value ssid dev wifi list", capture_output=True, text=True, check=True, shell=True)
        networks = set()
        for line in result.stdout.split('\n'):
            if not line.strip():
                continue
            networks.add(line.strip())  # 'line' represents SSID
        logging.info(f"[scan_networks] scanned networks: {networks}")
        return list(networks)
    except subprocess.CalledProcessError as e:
        logging.info(f"Error scanning networks: {e}")
        return None


async def connect_network(ssid: str, password: str) -> bool:
    try:
        logging.info(f"connecting to network {ssid}: {password}")
        subprocess.run(f"sudo nmcli dev wifi connect \"{ssid}\" password \"{password}\"", check=True, shell=True)
        time.sleep(NETWORK_CONNECT_DELAY)
        result = subprocess.run("sudo nmcli --get-value type,state,connection dev status", capture_output=True, text=True, check=True, shell=True)
        for line in result.stdout.split('\n'):
            if not line.strip():
                continue
            pattern = re.compile(r'^wifi:connected:(.+)$')
            match = pattern.match(line.strip())
            if match is not None:
                connected_ssid = match.group(1)
                return (connected_ssid == ssid)
        return False
    except subprocess.CalledProcessError as e:
        logging.info(f"Error connecting to network: {e}")
        return False
