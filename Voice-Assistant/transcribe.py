from faster_whisper import WhisperModel

def transcribe(filename):
    print("Loading model...")
    model_size = "small"
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    print("Model loaded.")

    print("Transcribing audio...")
    segments, info = model.transcribe(filename, beam_size=5)

    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

    text = "".join(segment.text for segment in segments)
    print(text)
    return text,info.language