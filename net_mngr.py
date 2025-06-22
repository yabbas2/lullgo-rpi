import subprocess
import time
import logging
import re
from hashlib import pbkdf2_hmac

# configure logging
logging.basicConfig(level=logging.INFO)

NETWORK_UP_DELAY = 2  # in seconds
NETWORK_SCAN_INTERVAL = 5  # in seconds
NETWORK_CONNECT_DELAY = 5  # in seconds


class NetMngr:
    def __init__(self):
        pass

    async def enable_network(self) -> bool:
        return False

    async def scan_network(self) -> list:
        return []

    async def connect_network(self, ssid: str, password: str) -> bool:
        return False


class WpaSupplicant(NetMngr):
    def __init__(self):
        super().__init__()

    def _wpa_psk(self, ssid, passphrase) -> str:
        return pbkdf2_hmac(
            "sha1",
            passphrase.encode("utf_8"),
            ssid.encode("utf_8"),
            4096,
            dklen=32,
        ).hex()

    async def enable_network(self) -> bool:
        try:
            subprocess.run("sudo rfkill unblock wifi", check=True, shell=True)
            subprocess.run("sudo ip link set dev wlan0 up", check=True, shell=True)
            time.sleep(NETWORK_UP_DELAY)
            return True
        except Exception as e:
            logging.info(f"Error enabling wifi: {e}")
            return False

    async def scan_network(self) -> list:
        try:
            subprocess.run("sudo wpa_cli -i wlan0 scan", check=True, shell=True)
            time.sleep(NETWORK_SCAN_INTERVAL)
            result = subprocess.run("sudo wpa_cli -i wlan0 scan_results", capture_output=True, text=True, check=True, shell=True)
            networks = set()
            for line in result.stdout.split('\n')[1:]:  # first line is header -> ignore
                if not line.strip():
                    continue
                pattern = re.compile(r'^[0-9a-zA-Z:]{17}\s+[0-9]+\s+[0-9-]+\s+\[\S+\]\s+(.+)$')
                match = pattern.match(line.strip())
                if match is not None:
                    networks.add(match.group(1))
            logging.info(f"[scan_networks] scanned networks: {networks}")
            return list(networks)
        except Exception as e:
            logging.info(f"Error scanning networks: {e}")
            return []

    async def connect_network(self, ssid: str, password: str) -> bool:
        try:
            logging.info(f"connecting to network {ssid}: {password}")
            net_id = subprocess.run("sudo wpa_cli -i wlan0 add_network", capture_output=True, text=True, check=True, shell=True)
            net_id = net_id.stdout.strip()
            logging.info(f"created new network: {net_id}")
            subprocess.run(f"sudo wpa_cli -i wlan0 set_network {net_id} ssid \\\"{ssid}\\\"", check=True, shell=True)
            subprocess.run(f"sudo wpa_cli -i wlan0 set_network {net_id} psk {self._wpa_psk(ssid, password)}", check=True, shell=True)
            subprocess.run(f"sudo wpa_cli -i wlan0 enable_network {net_id}", check=True, shell=True)
            subprocess.run(f"sudo wpa_cli -i wlan0 save_config", check=True, shell=True)
            time.sleep(NETWORK_CONNECT_DELAY)
            # check connection state
            result = subprocess.run("sudo wpa_cli -i wlan0 status", capture_output=True, text=True, check=True, shell=True)
            result = result.stdout.strip()
            pattern = re.compile(r'\bwpa_state=(.+)')
            match = pattern.match(result)
            if match is None or match.group(1) != "COMPLETED":
                return False
            return True
        except Exception as e:
            logging.info(f"Error connecting to network: {e}")
            return False


class NetworkManager(NetMngr):
    def __init__(self):
        super().__init__()

    async def enable_network(self) -> bool:
        try:
            subprocess.run("sudo nmcli radio wifi on", check=True, shell=True)
            time.sleep(NETWORK_UP_DELAY)
            return True
        except Exception as e:
            logging.info(f"Error enabling wifi: {e}")
            return False

    async def scan_network(self) -> list:
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
        except Exception as e:
            logging.info(f"Error scanning networks: {e}")
            return []

    async def connect_network(self, ssid: str, password: str) -> bool:
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
        except Exception as e:
            logging.info(f"Error connecting to network: {e}")
            return False
