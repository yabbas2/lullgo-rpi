"""
WebSocket Client
Sends baby cry detection messages
"""

import time
from tflite_support.task import audio
from tflite_support.task import core
from tflite_support.task import processor
from datetime import datetime
import asyncio
import websockets
import json
import logging

import sounddevice as sd
sd.default.device = 0
sd.default.channels = 2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BCD:
    def __init__(self, server_url, client_name="rpi-nurse.bcd"):
        """
        Initialize the WebSocket client

        Args:
            server_url (str): WebSocket server URL (e.g., ws://192.168.1.100:8765)
            client_name (str): Name of this client
        """
        # Initialize websocket parameters
        self.server_url = server_url
        self.client_name = client_name
        self.connection = None
        self.is_running = False
        self.reconnect_interval = 5
        self.last_bcd = time.time()
        # Initialize bcd parameters
        self.model_path = "/home/rpi/lullgo/models/yamnet.tflite"
        self.max_nof_results = 5
        self.overlap_factor = 0.5  # allowed range: ]0, 1[
        self.score_threshold = 0.3  # allowed range: [0, 1]
        self.cpu_threads = 4
        self.desired_classes = ["Screaming", "Baby laughter", "Crying, sobbing", "Baby cry, infant cry"]
        # Initialize the audio classification model
        self.base_options = core.BaseOptions(file_name=self.model_path, use_coral=False, num_threads=self.cpu_threads)
        self.classification_options = processor.ClassificationOptions(max_results=self.max_nof_results, score_threshold=self.score_threshold)
        self.options = audio.AudioClassifierOptions(base_options=self.base_options, classification_options=self.classification_options)
        self.classifier = audio.AudioClassifier.create_from_options(self.options)
        # Initialize the audio recorder and a tensor to store the audio input
        self.audio_record = self.classifier.create_audio_record()
        self.tensor_audio = self.classifier.create_input_tensor_audio()

    async def send_bcd_msg(self):
        """Send baby cry detection message to server"""
        tmp = time.time()
        if tmp - self.last_bcd < 2:
            # do not send bcd message yet
            return True
        self.last_bcd = tmp

        bcd_message = {
            'type': 'bcd',
            'client_name': self.client_name,
            'timestamp': datetime.now().isoformat(),
        }

        try:
            await self.connection.send(json.dumps(bcd_message))
            logger.info(f"BCD message sent to server at {datetime.now().strftime('%H:%M:%S')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send BCD message: {e}")
            return False

    async def bcd_main(self):
        """Continuously run inference on audio data acquired from the device."""

        # We'll try to run inference every interval_between_inference seconds.
        # This is usually half of the model's input length to create an overlap
        # between incoming audio segments to improve classification accuracy.
        input_length_in_second = float(len(self.tensor_audio.buffer)) / self.tensor_audio.format.sample_rate
        interval_between_inference = input_length_in_second * (1 - self.overlap_factor)
        pause_time = interval_between_inference * 0.1
        last_inference_time = time.time()

        # Start audio recording in the background.
        self.audio_record.start_recording()

        while self.is_running:
            # Wait until at least interval_between_inference seconds has passed since
            # the last inference.
            now = time.time()
            diff = now - last_inference_time
            if diff < interval_between_inference:
                await asyncio.sleep(pause_time)
                continue
            last_inference_time = now

            # Load the input audio and run classify.
            self.tensor_audio.load_from_audio_record(self.audio_record)
            result = self.classifier.classify(self.tensor_audio)

            # print(result)
            classification = result.classifications[0]
            result_list = [(category.category_name, category.score) for category in classification.categories]

            for res in result_list:
                if res[0] in self.desired_classes:
                    # print(f"{res[0]}: {res[1]}")
                    # print("==========================================")
                    self.is_running = await self.send_bcd_msg()

        # Free up resources
        self.audio_record.stop()

    async def connect(self):
        """Connect to the WebSocket server"""
        logger.info(f"Connecting to server at {self.server_url}")

        try:
            self.connection = await websockets.connect(self.server_url)
            logger.info(f"Connected to server successfully")

            # Start detection loop
            self.is_running = True
            bcd_task = asyncio.create_task(self.bcd_main())

            await asyncio.sleep(1)
            # Wait for task to complete
            await asyncio.gather(bcd_task)

        except ConnectionRefusedError:
            logger.error(f"Connection refused. Is the server running at {self.server_url}?")
        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            self.is_running = False
            if self.connection:
                await self.connection.close()

    async def run_with_reconnect(self):
        """Run client with automatic reconnection"""
        while True:
            try:
                await self.connect()
            except Exception as e:
                logger.error(f"Client error: {e}")

            logger.info(f"Attempting to reconnect in {self.reconnect_interval} seconds...")
            await asyncio.sleep(self.reconnect_interval)


def main():
    """Main function to run the client"""
    client = BCD(server_url="ws://parent.local:8765")

    try:
        asyncio.run(client.run_with_reconnect())
    except Exception as e:
        logger.error(f"Client error: {e}")


if __name__ == '__main__':
    main()
