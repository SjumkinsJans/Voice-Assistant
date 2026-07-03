from audio import *
from main import *
import pyaudio
import wave
import numpy as np
import openwakeword
from openwakeword.model import Model

# Instantiate the model(s)
model = Model()  # can also leave this argument empty to load all of the included pre-trained models
RATE = 16000
CHUNK = 1280 #80ms
audio = pyaudio.PyAudio()

stream_setting = {
    "format": pyaudio.paInt16,
    "channels": 1,
    "rate": RATE,
    "input": True,
    "frames_per_buffer": CHUNK
}

stream = audio.open(
    format= stream_setting["format"],
    channels= stream_setting["channels"],
    rate= stream_setting["rate"],
    input=True,
    frames_per_buffer=stream_setting["frames_per_buffer"]
)


print("listening...")
while True:
    data = stream.read(CHUNK, exception_on_overflow=False)
    frame = np.frombuffer(data, dtype=np.int16)
    prediction = model.predict(frame)

    if(prediction['alexa']) > 0.5:
        break
    if(prediction['hey_jarvis'] > 0.5):
        print("Wake word detected!")
        
