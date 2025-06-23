echo "[YA] stopping baby cry detection service"
sudo systemctl stop bcd.service

echo "[YA] starting gstreamer pipline (video & audio)"
gst-launch-1.0 rtspclientsink name=s location=rtsp://localhost:8554/feed rtspsrc location=rtsp://127.0.0.1:8554/cam latency=0 ! rtph264depay ! s.  alsasrc device=hw:0,0 ! audioconvert ! audioresample ! audio/x-raw,rate=48000,channels=2 ! opusenc bitrate=96000 ! s.
