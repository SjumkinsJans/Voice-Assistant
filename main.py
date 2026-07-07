import string

from audio import *
from transcribe import *
from tts import *

import os
stream_setting = {
    "format": pyaudio.paInt16,
    "channels": 1,
    "rate": 16000,
    "input": True,
    "frames_per_buffer": 1280, #80ms
    "record_seconds": 3
}

p = pyaudio.PyAudio()
model = Model()

stream = p.open(format=stream_setting["format"],
            channels=stream_setting["channels"],
            rate=stream_setting["rate"],
            input=True,
            frames_per_buffer=stream_setting["frames_per_buffer"],
            )


while True:
    filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".wav"
    print("Listening...")
    status = record(filename,stream,stream_setting,model,p)
    if(status == 0):
        break
    text,language = transcribe(filename)
    #os.remove(filename)
    if(text[-1] == "."):
        text = text[:-1]

    clean_text = text.lower().strip().translate(str.maketrans('', '', string.punctuation))

    print(repr(clean_text) + " " + "hi")
    if(clean_text == "hi" or clean_text == "hello" or clean_text == "hey"):
        voice("Good day Mr.Bezos", "en")
        play("output.wav")
    elif(clean_text == "die"):
        break
    else:
        voice(text, language)
        play("output.wav")
    #os.remove("output.wav")
    model = Model()