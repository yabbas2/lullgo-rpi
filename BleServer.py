import distro
import asyncio
import logging
from typing import Any, Dict
from bless import (
    BlessServer,
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions,
)
from NetMngr import *

logging.basicConfig(level=logging.INFO)


class BleServer:
    _service_map: Dict = {
        "WIFI": "a97bb3e5-5f0c-495e-a87d-d642e77f1216"
    }
    _characteristic_map: Dict = {
        "SSID": "4a2d084a-7c2a-4fb5-9122-700858ed37c0",
        "PASSWORD": "8b107cf0-be4f-4aa9-b7ac-529779d1cc33",
        "CONNECT_STATUS": "6cf12fea-c7dc-47c4-a57d-79a3ba7ddfec",
        "NETWORKS": "a324d143-e23a-4377-ad7c-bd2b89da0e15"
    }
    _gatt: Dict = {
        "a97bb3e5-5f0c-495e-a87d-d642e77f1216": {  # WIFI service
            "4a2d084a-7c2a-4fb5-9122-700858ed37c0": {  # WIFI SSID
                "Properties": (GATTCharacteristicProperties.write | GATTCharacteristicProperties.write_without_response),
                "Permissions": GATTAttributePermissions.writeable,
                "Value": None,
            },
            "8b107cf0-be4f-4aa9-b7ac-529779d1cc33": {  # WIFI PASSWORD
                "Properties": (GATTCharacteristicProperties.write | GATTCharacteristicProperties.write_without_response),
                "Permissions": GATTAttributePermissions.writeable,
                "Value": None,
            },
            "a324d143-e23a-4377-ad7c-bd2b89da0e15": {  # WIFI NETWORKS
                "Properties": (GATTCharacteristicProperties.read | GATTCharacteristicProperties.notify),
                "Permissions": GATTAttributePermissions.readable,
                "Value": None,
            },
            "6cf12fea-c7dc-47c4-a57d-79a3ba7ddfec": {  # WIFI connection status
                "Properties": GATTCharacteristicProperties.notify,
                "Permissions": GATTAttributePermissions.readable,
                "Value": None,
            }
        }
    }

    _scan_networks = False
    _recvd_wifi_ssid = False
    _recvd_wifi_password = False

    def __init__(self, net_mngr: NetMngr):
        self._server = BlessServer(name="lullgo-BLE")
        self._net_mngr = net_mngr

    @staticmethod
    def read_callback(characteristic: BlessGATTCharacteristic, **kwargs) -> bytearray:
        """Handle read request"""
        logging.info(f"Read request received {characteristic.uuid}")
        if (characteristic.uuid == BleServer._characteristic_map["NETWORKS"]):
            BleServer._scan_networks = True
            return b'ack'
        return b''

    @staticmethod
    def write_callback(characteristic: BlessGATTCharacteristic, value: Any, **kwargs):
        """Handle write request"""
        logging.info(f"Write request received: {value}")
        if characteristic.uuid == BleServer._characteristic_map["SSID"]:
            BleServer._recvd_wifi_ssid = True
            characteristic.value = value
        if characteristic.uuid == BleServer._characteristic_map["PASSWORD"]:
            BleServer._recvd_wifi_password = True
            characteristic.value = value

    @staticmethod
    def notify(server: BlessServer, key: str, value: bytearray):
        logging.info(f"Notification to send: {value}")
        service_uuid: str = BleServer._service_map[key.split('.')[0]]
        characteristic_uuid: str = BleServer._characteristic_map[key.split('.')[1]]
        server.get_characteristic(characteristic_uuid).value = value
        server.update_value(service_uuid, characteristic_uuid)

    async def _setup(self):
        """Setup the BLE GATT server with configuration"""
        self._server.read_request_func = BleServer.read_callback
        self._server.write_request_func = BleServer.write_callback
        await self._server.add_gatt(BleServer._gatt)
        await self._server.start()

    async def _handle_scan_networks(self):
        """Handle scanning networks via WIFI helper functions"""
        result: bool = await self._net_mngr.enable_network()
        if not result:
            BleServer.notify(self._server, "WIFI.CONNECT_STATUS", b'nok')
            return
        networks: list = await self._net_mngr.scan_network()
        BleServer.notify(self._server, "WIFI.NETWORKS", bytearray("\n".join(networks), encoding="utf-8"))

    async def _handle_wifi_connect(self):
        """Handle connecting to network via WIFI helper functions"""
        ssid_char_uuid = BleServer._characteristic_map["SSID"]
        password_char_uuid = BleServer._characteristic_map["PASSWORD"]
        result = await self._net_mngr.connect_network(self._server.get_characteristic(ssid_char_uuid).value.decode("utf-8"), self._server.get_characteristic(password_char_uuid).value.decode("utf-8"))
        BleServer.notify(self._server, "WIFI.CONNECT_STATUS", b'ok' if result else b'nok')

    async def run(self):
        """Start the BLE server"""
        await self._setup()
        logging.info("BLE GATT server started. Waiting for connections...")
        try:
            while True:
                await asyncio.sleep(1)
                if BleServer._scan_networks:
                    BleServer._scan_networks = False
                    await self._handle_scan_networks()
                if BleServer._recvd_wifi_ssid and BleServer._recvd_wifi_password:
                    BleServer._recvd_wifi_ssid = False
                    BleServer._recvd_wifi_password = False
                    await self._handle_wifi_connect()
        except asyncio.CancelledError:
            logging.info("BLE GATT server shutting down...")
            await self._server.stop()


async def main():
    os_ver = distro.major_version()
    if int(os_ver) > 11:  # after bullseye release
        net_mngr = NetworkManager()
    else:  # bullseye and previous releases
        net_mngr = WpaSupplicant()
    ble_server = BleServer(net_mngr)
    await ble_server.run()


if __name__ == "__main__":
    asyncio.run(main())
