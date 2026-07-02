from faster_whisper import WhisperModel
from huggingface_hub import login

# access token : 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


print("Loading model...")

login("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")
model_size = "medium"
model = WhisperModel(model_size, device="cpu", compute_type="int8")
print("Model loaded.")

print("Transcribing audio...")
segments, info = model.transcribe("lv.mp3", beam_size=5)

print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))