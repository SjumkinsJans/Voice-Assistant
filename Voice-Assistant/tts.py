import subprocess
from unittest import result


def voice(text): 
    result = subprocess.run(
        [
        "piper",
        "--model", "en_US-lessac-medium.onnx",
        "--output_file", "output.wav"
        ],
        input=text.encode("utf-8"),
        capture_output=True
    )

    print(result.stderr.decode())

voice("Hello, this is a test of the text-to-speech function.")