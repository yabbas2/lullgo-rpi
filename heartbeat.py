"""
WebSocket Client
Sends heartbeat messages every 2 seconds and listens for acknowledgements
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime
import time
from gpiozero import LED

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Heartbeat:
    def __init__(self, server_url, client_name="rpi-nurse.heartbeat"):
        """
        Initialize the WebSocket client

        Args:
            server_url (str): WebSocket server URL (e.g., ws://192.168.1.100:8765)
            client_name (str): Name of this client
        """
        self._server_url = server_url
        self._client_name = client_name
        self._connection = None
        self._heartbeat_interval = 2  # seconds
        self._reconnect_interval = 5  # seconds
        self._is_running = False
        self._missed_heartbeats = 0
        self._max_missed_heartbeats = 5
        self._led = LED(26)

    async def _send_heartbeat(self):
        """Send heartbeat message to server"""
        heartbeat_message = {
            'type': 'heartbeat',
            'client_name': self._client_name,
            'timestamp': datetime.now().isoformat(),
        }

        try:
            await self._connection.send(json.dumps(heartbeat_message))
            logger.info(f"Heartbeat sent to server at {datetime.now().strftime('%H:%M:%S')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
            return False

    async def _listen_for_messages(self):
        """Listen for messages from server"""
        try:
            async for message in self._connection:
                try:
                    data = json.loads(message)

                    if data.get('type') == 'acknowledgement':
                        logger.info(f"acknowledgement received from server: {data.get('message')}")
                        logger.info(f"Server: {data.get('server_name')}, Heartbeat time: {data.get('received_heartbeat')}")
                        self._led.on()
                    else:
                        logger.warning(f"Unknown message type from server: {data.get('type')}")

                except json.JSONDecodeError:
                    logger.error("Invalid JSON received from server")

        except websockets.exceptions.ConnectionClosed as e:
            logger.error(f"Connection closed: {e}")
            return False

        return True

    async def _heartbeat_loop(self):
        """Main heartbeat loop"""
        while self._is_running:
            # Send heartbeat
            success = await self._send_heartbeat()

            if not success:
                self._missed_heartbeats += 1
                logger.warning(f"Missed heartbeat count: {self._missed_heartbeats}")
                self._led.blink()

                if self._missed_heartbeats >= self._max_missed_heartbeats:
                    logger.error(f"Too many missed heartbeats. Reconnecting...")
                    # self._led.off()
                    return False
            else:
                # Reset missed heartbeat counter on successful send
                self._missed_heartbeats = 0

            # Wait for the interval before sending next heartbeat
            await asyncio.sleep(self._heartbeat_interval)

        return True

    async def _connect(self):
        """Connect to the WebSocket server"""
        logger.info(f"Connecting to server at {self._server_url}")

        try:
            self._connection = await websockets.connect(self._server_url)
            logger.info(f"Connected to server successfully")

            # Start listening for messages
            listener_task = asyncio.create_task(self._listen_for_messages())

            # Start heartbeat loop
            self._is_running = True
            heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            await asyncio.sleep(1)
            # Wait for tasks to complete
            await asyncio.gather(listener_task, heartbeat_task)

        except ConnectionRefusedError:
            logger.error(f"Connection refused. Is the server running at {self._server_url}?")
        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            self._is_running = False
            if self._connection:
                await self._connection.close()

    async def run_with_reconnect(self):
        """Run client with automatic reconnection"""
        while True:
            try:
                await self._connect()
            except Exception as e:
                logger.error(f"Client error: {e}")

            logger.info(f"Attempting to reconnect in {self._reconnect_interval} seconds...")
            await asyncio.sleep(self._reconnect_interval)


def main():
    """Main function to run the client"""
    client = Heartbeat(server_url="ws://parent.local:8765")

    try:
        asyncio.run(client.run_with_reconnect())
    except Exception as e:
        logger.error(f"Client error: {e}")


if __name__ == "__main__":
    main()
