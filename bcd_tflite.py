import time
from tflite_support.task import audio
from tflite_support.task import core
from tflite_support.task import processor

import sounddevice as sd
sd.default.device = 0  # seeed respeaker 2-mics
sd.default.channels = 2

MODEL_PATH = "./models/yamnet.tflite"
MAX_NOF_RESULTS = 5
OVERLAP_FACTOR = 0.5
SCORE_THRESHOLD = 0.5
CPU_THREADS = 4
DESIRED_CLASSES = ["Screaming", "Baby laughter", "Crying, sobbing", "Baby cry, infant cry"]


def run(model: str, max_results: int, score_threshold: float,
        overlapping_factor: float, num_threads: int) -> None:
    """Continuously run inference on audio data acquired from the device.

    Args:
        model: Name of the TFLite audio classification model.
        max_results: Maximum number of classification results to display.
        score_threshold: The score threshold of classification results.
        overlapping_factor: Target overlapping between adjacent inferences.
        num_threads: Number of CPU threads to run the model.
    """

    if (overlapping_factor <= 0) or (overlapping_factor >= 1.0):
        raise ValueError('Overlapping factor must be between 0 and 1.')

    if (score_threshold < 0) or (score_threshold > 1.0):
        raise ValueError('Score threshold must be between (inclusive) 0 and 1.')

    # Initialize the audio classification model.
    base_options = core.BaseOptions(file_name=model, use_coral=False, num_threads=num_threads)
    classification_options = processor.ClassificationOptions(max_results=max_results, score_threshold=score_threshold)
    options = audio.AudioClassifierOptions(base_options=base_options, classification_options=classification_options)
    classifier = audio.AudioClassifier.create_from_options(options)

    # Initialize the audio recorder and a tensor to store the audio input.
    audio_record = classifier.create_audio_record()
    tensor_audio = classifier.create_input_tensor_audio()

    # We'll try to run inference every interval_between_inference seconds.
    # This is usually half of the model's input length to create an overlapping
    # between incoming audio segments to improve classification accuracy.
    input_length_in_second = float(len(tensor_audio.buffer)) / tensor_audio.format.sample_rate
    interval_between_inference = input_length_in_second * (1 - overlapping_factor)
    pause_time = interval_between_inference * 0.1
    last_inference_time = time.time()

    # Start audio recording in the background.
    audio_record.start_recording()

    # Loop until the user close the classification results plot.
    while True:
        # Wait until at least interval_between_inference seconds has passed since
        # the last inference.
        now = time.time()
        diff = now - last_inference_time
        if diff < interval_between_inference:
            time.sleep(pause_time)
            continue
        last_inference_time = now

        # Load the input audio and run classify.
        tensor_audio.load_from_audio_record(audio_record)
        result = classifier.classify(tensor_audio)

        # print(result)
        classification = result.classifications[0]
        result_list = [(category.category_name, category.score) for category in classification.categories]

        for res in result_list:
            if res[0] in DESIRED_CLASSES:
                print(f"{res[0]}: {res[1]}")
                print("==========================================")


def main():
    run(MODEL_PATH, MAX_NOF_RESULTS, SCORE_THRESHOLD, OVERLAP_FACTOR, CPU_THREADS)


if __name__ == '__main__':
    main()
