import asyncio
import logging

from typing import Any, Dict
from bless import (
    BlessServer,
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions,
)

# configure logging
logging.basicConfig(level=logging.INFO)


class BleGattServer:
    def __init__(self):
        self.server = BlessServer(name="DietPi-BLE")
        # init GATT structure of services and characteristics
        self.gatt: Dict = {
            "A97BB3E5-5F0C-495E-A87D-D642E77F1216": {  # WIFI service
                "4A2D084A-7C2A-4FB5-9122-700858ED37C0": {  # WIFI SSID
                    "Properties": (GATTCharacteristicProperties.write | GATTCharacteristicProperties.write_without_response),
                    "Permissions": GATTAttributePermissions.writeable,
                    "Value": None,
                },
                "8B107CF0-BE4F-4AA9-B7AC-529779D1CC33": {  # WIFI PASSWORD
                    "Properties": (GATTCharacteristicProperties.write | GATTCharacteristicProperties.write_without_response),
                    "Permissions": GATTAttributePermissions.writeable,
                    "Value": None,
                },
                "6CF12FEA-C7DC-47C4-A57D-79A3BA7DDFEC": {  # WIFI connection status
                    "Properties": GATTCharacteristicProperties.notify,
                    "Permissions": GATTAttributePermissions.readable,
                    "Value": None,
                }
            }
        }

    @staticmethod
    def read_callback(characteristic: BlessGATTCharacteristic, **kwargs) -> bytearray:
        """Handle read request"""
        logging.info("Read request received")
        return characteristic.value

    @staticmethod
    def write_callback(characteristic: BlessGATTCharacteristic, value: Any, **kwargs):
        """Handle write request"""
        logging.info(f"Write request received: {value}")
        characteristic.value = value

    @staticmethod
    def notify(server: BlessServer, value: bytearray):
        server.get_characteristic("6CF12FEA-C7DC-47C4-A57D-79A3BA7DDFEC").value = value
        server.update_value("A97BB3E5-5F0C-495E-A87D-D642E77F1216", "6CF12FEA-C7DC-47C4-A57D-79A3BA7DDFEC")

    async def setup(self):
        """Setup the BLE GATT server with configuration"""
        self.server.read_request_func = BleGattServer.read_callback
        self.server.write_request_func = BleGattServer.write_callback
        await self.server.add_gatt(self.gatt)
        await self.server.start()

    async def run(self):
        """Start the BLE server"""
        await self.setup()
        logging.info("BLE GATT server started. Waiting for connections...")
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logging.info("BLE GATT server shutting down...")
            await self.server.stop()


# run the BLE GATT server
async def main():
    server = BleGattServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
