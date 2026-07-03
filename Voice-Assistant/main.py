from audio import *
from transcribe import *
from tts import *

import os
filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".wav"
record(filename)
transcribe(filename)
os.remove(filename)