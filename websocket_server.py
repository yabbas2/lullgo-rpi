"""
WebSocket Server
Listens for heartbeat messages and sends acknowledgements
Listens for baby cry detection messages
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebsocketServer:
    def __init__(self, host='0.0.0.0', port=8765):
        """
        Initialize the WebSocket server

        Args:
            host (str): Host address to bind to (default: all interfaces)
            port (int): Port to listen on
        """
        self.host = host
        self.port = port
        self.clients = set()
        self.client_info = {}

    async def handle_client(self, websocket):
        """
        Handle incoming WebSocket connections

        Args:
            websocket: WebSocket connection object
            path: Request path
        """
        client_id = id(websocket)
        client_address = websocket.remote_address
        logger.info(f"New client connected: {client_address}")
        self.clients.add(websocket)

        try:
            async for message in websocket:
                try:
                    # Parse the incoming message
                    data = json.loads(message)

                    if data.get('type') == 'heartbeat':
                        # Extract client information
                        client_name = data.get('client_name', 'Unknown')
                        timestamp = data.get('timestamp', '')

                        # Log the heartbeat
                        logger.info(f"Heartbeat received from {client_name} at {timestamp}")

                        # Prepare acknowledgement
                        ack_message = {
                            'type': 'acknowledgement',
                            'server_name': 'rpi-parent',
                            'timestamp': datetime.now().isoformat(),
                            'received_heartbeat': timestamp,
                            'message': 'Heartbeat received and acknowledged'
                        }

                        # Send acknowledgement back to client
                        await websocket.send(json.dumps(ack_message))
                        logger.info(f"acknowledgement sent to {client_name}")

                        # Store client info
                        self.client_info[client_id] = {
                            'name': client_name,
                            'address': client_address,
                            'last_heartbeat': timestamp,
                            'last_seen': datetime.now().isoformat()
                        }
                    elif data.get('type') == 'bcd':
                        # Extract client information
                        client_name = data.get('client_name', 'Unknown')
                        timestamp = data.get('timestamp', '')

                        # Log the bcd message
                        logger.info(f"BCD message received from {client_name} at {timestamp}")

                        # Store client info
                        self.client_info[client_id] = {
                            'name': client_name,
                            'address': client_address,
                            'last_bcd': timestamp,
                            'last_seen': datetime.now().isoformat()
                        }
                    else:
                        logger.warning(f"Unknown message type from {client_address}: {data.get('type')}")

                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received from {client_address}")

        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Client disconnected: {client_address}, reason: {e}")
        finally:
            self.clients.remove(websocket)
            if client_id in self.client_info:
                del self.client_info[client_id]
            logger.info(f"Active connections: {len(self.clients)}")

    def get_uptime(self):
        """Get server uptime (simplified version)"""
        # In a real implementation, you might track when the server started
        return "Server started recently"

    async def periodic_status(self):
        """Periodically log server status"""
        while True:
            await asyncio.sleep(30)  # Log every 30 seconds
            logger.info(f"Server status - Active connections: {len(self.clients)}")

    async def run(self):
        """Run the WebSocket server"""
        logger.info(f"Server will listen on all interfaces {self.host}:{self.port}")

        # Start periodic status logging
        status_task = asyncio.create_task(self.periodic_status())

        # Start WebSocket server
        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info("WebSocket server is running.")
            # Keep the server running
            await asyncio.Future()


def main():
    """Main function to run the server"""
    server = WebsocketServer()

    try:
        asyncio.run(server.run())
    except Exception as e:
        logger.error(f"Server error: {e}")


if __name__ == "__main__":
    main()
