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
import numpy as np
import threading
import queue
import soundfile as sf
from gpiozero import LED

import sounddevice as sd
sd.default.device = 0
sd.default.channels = 1

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AudioPlayer:
    """Non-blocking audio player that manages audio playback in a separate thread"""

    def __init__(self):
        """Initialize the audio player"""
        self._audio_file = None
        self._audio_data = None
        self._sample_rate = None
        self._playback_queue = queue.Queue()
        self._is_playing = False
        self._playback_thread = None
        self._stop_event = threading.Event()
        self._audio_list = [
            "/home/rpi/lullgo/sounds/adel_shakal.wav",
            "/home/rpi/lullgo/sounds/waaa2_1.wav",
            "/home/rpi/lullgo/sounds/waaa2_2.wav",
        ]

        # Start the playback thread
        self._start__playback_thread()

    def _load_audio(self):
        """Load the audio file randomly from a list of audio files"""
        try:
            self._audio_file = np.random.choice(self._audio_list)
            self._audio_data, self._sample_rate = sf.read(self._audio_file, dtype='float32')
            logger.info(f"Loaded audio file: {self._audio_file}, " f"Sample rate: {self._sample_rate}")
        except Exception as e:
            logger.error(f"soundfile not available: {e}")

    def _start__playback_thread(self):
        """Start the audio playback thread"""
        self._stop_event.clear()
        self._playback_thread = threading.Thread(
            target=self._playback_worker,
            daemon=True
        )
        self._playback_thread.start()
        logger.info("Audio playback thread started")

    def _playback_worker(self):
        """Worker thread that handles audio playback"""
        while not self._stop_event.is_set():
            try:
                # Wait for play command (with timeout to check stop event)
                play_signal = self._playback_queue.get(timeout=0.1)
                if play_signal == "PLAY":
                    # Load audio file randomly
                    self._load_audio()

                    self._is_playing = True
                    logger.info("Starting audio playback")

                    # Play audio - this will block until playback is complete
                    # but that's OK since we're in a separate thread
                    sd.play(self._audio_data, self._sample_rate)
                    sd.wait()  # Wait for playback to finish

                    logger.info("Audio playback finished")
                    self._is_playing = False

            except queue.Empty:
                # No play command, just continue
                continue
            except Exception as e:
                logger.error(f"Error in playback worker: {e}")
                self._is_playing = False

    def play(self):
        """Trigger audio playback (non-blocking)"""
        if self._is_playing:
            logger.info("Audio is already playing, skipping new request")
            return False

        # Add play command to queue (non-blocking)
        try:
            self._playback_queue.put_nowait("PLAY")
            logger.info("Audio play command queued")
            return True
        except queue.Full:
            logger.warning("Playback queue is full")
            return False

    def is_playing(self):
        """Check if audio is currently playing"""
        return self._is_playing

    def stop(self):
        """Stop audio playback"""
        if self._is_playing:
            sd.stop()
            self._is_playing = False
            logger.info("Audio playback stopped")

    def shutdown(self):
        """Shutdown the audio player"""
        self.stop()
        self._stop_event.set()
        if self._playback_thread:
            self._playback_thread.join(timeout=1.0)
        logger.info("Audio player shutdown complete")


class WebsocketServer:
    def __init__(self, host='0.0.0.0', port=8765):
        """
        Initialize the WebSocket server

        Args:
            host (str): Host address to bind to (default: all interfaces)
            port (int): Port to listen on
        """
        self._host = host
        self._port = port
        self._clients = set()
        self._client_info = {}
        self._led = LED(26)

        # Initialize audio player
        self._audio_player = AudioPlayer()

    async def _handle_client(self, websocket):
        """
        Handle incoming WebSocket connections

        Args:
            websocket: WebSocket connection object
        """
        client_id = id(websocket)
        client_address = websocket.remote_address
        logger.info(f"New client connected: {client_address}")
        self._clients.add(websocket)

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
                        self._client_info[client_id] = {
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
                        self._client_info[client_id] = {
                            'name': client_name,
                            'address': client_address,
                            'last_bcd': timestamp,
                            'last_seen': datetime.now().isoformat()
                        }

                        # Play audio
                        if not self._audio_player.is_playing():
                            self._audio_player.play()
                    else:
                        logger.warning(f"Unknown message type from {client_address}: {data.get('type')}")

                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received from {client_address}")

        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Client disconnected: {client_address}, reason: {e}")
        finally:
            self._clients.remove(websocket)
            if client_id in self._client_info:
                del self._client_info[client_id]
            logger.info(f"Active connections: {len(self._clients)}")

    async def _periodic_status(self):
        """Periodically check server status"""
        while True:
            await asyncio.sleep(3)
            logger.info(f"Server status - Active connections: {len(self._clients)}")
            if len(self._clients) != 0:
                self._led.on()
            else:
                self._led.blink()

    async def run(self):
        """Run the WebSocket server"""
        logger.info(f"Server will listen on all interfaces {self._host}:{self._port}")

        # Start periodic status logging
        status_task = asyncio.create_task(self._periodic_status())

        # Start WebSocket server
        async with websockets.serve(self._handle_client, self._host, self._port):
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
