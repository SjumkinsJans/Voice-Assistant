import subprocess


def voice(text, language):
    switcher = {
        "en": "en_US-lessac-medium.onnx",
        "ru": "ru_RU-dmitri-medium.onnx",
        "lv": "lv_LV-aivars-medium.onnx"
    } 
    model = switcher.get(language, "en_US-lessac-medium.onnx")
    result = subprocess.run(
        [
        "piper",
        "--model",
        model,
        ],
        input=text.encode("utf-8"),
        capture_output=True
    )