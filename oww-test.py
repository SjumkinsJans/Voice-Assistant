import openwakeword
from openwakeword.model import Model

openwakeword.utils.download_models()

model = Model(
    wakeword_models=['hey_jarvis']
)

# frame = my-function_to-get_frame()
# prediction = model.predict(frame)
