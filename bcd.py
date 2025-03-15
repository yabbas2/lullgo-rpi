import sounddevice as sd
import numpy as np
from scipy.signal import butter, lfilter
import time

# Configuration
SAMPLE_RATE = 16000      # 16 kHz (sufficient for baby cry frequencies)
CHUNK_DURATION = 4       # Process 4-second audio chunks
CHUNK_SIZE = SAMPLE_RATE * CHUNK_DURATION
FREQ_MIN = 300           # Baby cry frequency range (Hz)
FREQ_MAX = 600
RMS_THRESHOLD = 15     # Minimum loudness (adjust based on testing)
COOLDOWN = 10            # Seconds between alerts
DEVICE_ID = 0            # Default device


# High-pass filter to remove frequencies below 100 Hz
def butter_highpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return b, a


def highpass_filter(data, cutoff=100, fs=SAMPLE_RATE, order=5):
    b, a = butter_highpass(cutoff, fs, order=order)
    return lfilter(b, a, data)


def analyze_audio(audio_chunk):
    """Check if audio matches baby cry characteristics"""
    print("Analyzing audio chunk...")

    audio_chunk = highpass_filter(audio_chunk, cutoff=200)
    window = np.hanning(len(audio_chunk))
    audio_windowed = audio_chunk * window

    fft = np.fft.rfft(audio_windowed)
    freqs = np.fft.rfftfreq(len(audio_windowed), 1 / SAMPLE_RATE)

    idx = np.where((freqs >= FREQ_MIN) & (freqs <= FREQ_MAX))[0]
    if len(idx) == 0:
        return False

    rms_band = np.sqrt(np.mean(np.abs(fft[idx])**2))
    print("RMS: ", rms_band)
    if rms_band < RMS_THRESHOLD:
        return False

    dominant_freq = freqs[idx][np.argmax(np.abs(fft[idx]))]
    print("Dominant frequency: ", dominant_freq)

    return FREQ_MIN <= dominant_freq <= FREQ_MAX


def detect_baby_cry():
    print("Listening for baby cries (4-second chunks)...")
    last_alert = 0

    with sd.InputStream(
        device=DEVICE_ID,
        samplerate=SAMPLE_RATE,
        channels=2,
        dtype=np.float32
    ) as stream:
        while True:
            # Read 4 seconds of audio
            audio_chunk, _ = stream.read(CHUNK_SIZE)
            audio_chunk = audio_chunk.flatten()

            # Check for baby cry
            if analyze_audio(audio_chunk):
                if (time.time() - last_alert) >= COOLDOWN:
                    print("Baby cry detected!")
                    last_alert = time.time()


if __name__ == "__main__":
    detect_baby_cry()
