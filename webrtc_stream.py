from av import VideoFrame
import asyncio
from aiortc import RTCPeerConnection, VideoStreamTrack, RTCSessionDescription, RTCIceCandidate
from picamera2 import Picamera2
import json
import websockets
import time
import cv2


class PiCameraVideoTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.camera = Picamera2()

        # Configure for low-latency video streaming
        config = self.camera.create_video_configuration(
            main={
                "size": (640, 480),
                "format": "RGB888"  # Explicit format specification
            },
            buffer_count=6  # Optimal for RPI Zero 2
        )

        self.camera.configure(config)
        self.camera.start()
        self.last_frame_time = time.monotonic()
        self.frame_interval = 1 / 30

    async def recv(self):
        try:
            # Calculate time since last frame
            now = time.monotonic()
            elapsed = now - self.last_frame_time
            if elapsed < self.frame_interval:
                await asyncio.sleep(self.frame_interval - elapsed)

            # Capture frame synchronously (picamera2 isn't async-native)
            array = self.camera.capture_array("main")

            # Convert RGB to BGR for OpenCV compatibility
            frame = cv2.cvtColor(array, cv2.COLOR_RGB2BGR)

            # Create AV VideoFrame with proper timing
            av_frame = VideoFrame.from_ndarray(frame, format="bgr24")
            av_frame.pts = int(time.monotonic() * 90000)  # 90kHz clock
            av_frame.time_base = "1/90000"

            self.last_frame_time = time.monotonic()
            return av_frame

        except Exception as e:
            print(f"Frame capture error: {str(e)}")
            raise


async def run():
    pc = RTCPeerConnection()
    pc.addTransceiver("video", direction="sendonly")

    ws = await websockets.connect('ws://localhost:8080/ws')
    await ws.send(json.dumps({'type': 'register', 'id': 'streamer'}))

    @pc.on("ice_candidate")
    def on_ice_candidate(candidate):
        print("Sending ICE candidate")
        asyncio.create_task(ws.send(json.dumps({
            'type': 'ice',
            'from': 'streamer',
            'candidate': candidate.to_json()
        })))

    pc.addTrack(PiCameraVideoTrack())

    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    pc.localDescription.sdp = pc.localDescription.sdp.replace(
        'a=setup:actpass', 'a=setup:active'
    )
    pc.localDescription.sdp = pc.localDescription.sdp.replace(
        'a=fmtp:99 profile-level-id=42001f',
        'a=fmtp:99 profile-level-id=42e01f'
    )
    await ws.send(json.dumps({
        'type': 'offer',
        'from': 'streamer',
        'sdp': pc.localDescription.sdp
    }))

    while True:
        try:
            msg = json.loads(await ws.recv())
            if msg['type'] == 'answer':
                await pc.setRemoteDescription(
                    RTCSessionDescription(sdp=msg['sdp'], type='answer'))
            elif msg['type'] == 'ice':
                try:
                    # Extract candidate components
                    candidate_dict = msg['candidate']
                    candidate_str = candidate_dict['candidate']

                    # Create RTCIceCandidate properly
                    candidate = RTCIceCandidate(
                        foundation=candidate_str.split()[0],
                        component=int(candidate_str.split()[1]),
                        protocol=candidate_str.split()[2].lower(),
                        priority=int(candidate_str.split()[3]),
                        ip=candidate_str.split()[4],
                        port=int(candidate_str.split()[5]),
                        type=candidate_str.split()[7],
                        sdpMid=candidate_dict.get('sdpMid', '0'),
                        sdpMLineIndex=candidate_dict.get('sdpMLineIndex', 0)
                    )
                    await pc.addIceCandidate(candidate)
                    print("Added ICE candidate successfully")
                except Exception as e:
                    print(f"Error adding ICE candidate: {str(e)}")
        except websockets.exceptions.ConnectionClosed:
            print("Reconnecting...")
            await asyncio.sleep(2)
            pc = RTCPeerConnection()  # Reset connection
            await run()  # Restart

asyncio.run(run())
