# Lullgo (Raspberry PI Zero 2W edition)

## Python

Version 3.9.0 + packages in requirements.txt

## Integration with INMP441

Using INMP441 I2S mic requires patching tflite_support package located at <pyvenv>/lib/python3.9/site-packages/tensorflow_lite_support/python/task/audio/core/audio_record.py

1. add: `from scipy.signal import resample`

2. in `__init__` method: initialize sounddevice audio stream with proper values (in the call to `sd.InputStream`): channels=2, samplerate=48000

3. in `audio_callback` method: resample audio stream from 48khz to 16khz:

```
original_sr = 48000
target_sr = 16000
ratio = target_sr / original_sr
target_num_samples = int(len(data[:, 0]) * ratio)
resampled_data = resample(data[:, 0], target_num_samples)
resampled_data = resampled_data.reshape(-1, 1)
```
