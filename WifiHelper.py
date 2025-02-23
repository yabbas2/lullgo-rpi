import subprocess
import time
import logging

# configure logging
logging.basicConfig(level=logging.INFO)

NETWORK_SCAN_INTERVAL = 10  # in seconds


def enable_network_if() -> bool:
    try:
        subprocess.run(['sudo', 'rfkill', 'unblock', 'wifi'], check=True)
        subprocess.run(['sudo', 'ip', 'link', 'set', 'dev', 'wlan0', 'up'], check=True)
        subprocess.run(['sudo', 'systemctl', 'start', 'wpa_supplicant'], check=True)
        subprocess.run(['sudo', 'systemctl', 'start', 'dhcpcd'], check=True)
        time.sleep(2)
        return True
    except subprocess.CalledProcessError as e:
        logging.info(f"Error enabling WIFI interface: {e}")
        return False


async def scan_networks() -> list | None:
    try:
        subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'scan_interval', str(NETWORK_SCAN_INTERVAL)], check=True)
        subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'scan'], check=True)
        time.sleep(NETWORK_SCAN_INTERVAL)
        result = subprocess.run(['sudo', 'wpa_cli', '-i', 'wlan0', 'scan_results'], capture_output=True, text=True, check=True)
        networks = set()
        for line in result.stdout.split('\n')[1:]:  # first line is header -> ignore
            if not line.strip():
                continue
            parts = line.split('\t')
            # expected result table format:
            # 0         1           2               3       4
            # bssid     frequency   signal_level    flags   SSID
            if len(parts) < 5:
                continue
            ssid = parts[4]
            if ssid == '':
                continue
            networks.add(ssid)
        logging.info(f"[scan_networks] scanned networks: {networks}")
        return list(networks)
    except subprocess.CalledProcessError as e:
        logging.info(f"Error scanning networks: {e}")
        return None
