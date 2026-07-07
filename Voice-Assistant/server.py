"""
Minimal working round-trip test:
  phone records -> POST /talk -> transcribe -> speak back "I heard: <text>" -> phone plays it

Install:
    pip install flask faster-whisper pyttsx3

Run:
    python server_talk_endpoint.py
Then from your PHONE (same wifi), browse to:
    http://<this-machine's-LAN-IP>:5000
(use ipconfig/ifconfig to find that IP — 127.0.0.1 will NOT work from another device)
"""

import os
import string
import uuid
from flask import Flask, request, send_file, render_template_string
from faster_whisper import WhisperModel

from tts import voice

app = Flask(__name__)

# Load the STT model ONCE at startup — loading it per-request would be very slow
whisper_model = WhisperModel("small", device="cpu", compute_type="int8")

UPLOAD_DIR = "uploads"
REPLY_DIR = "replies"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPLY_DIR, exist_ok=True)


# ---------- simple test page with record button ----------
PAGE = """
<!doctype html>
<html><body>
<button id="rec">🎤 Hold to talk</button>
<p id="status"></p>
<audio id="player" autoplay></audio>
<script>
let mediaRecorder, chunks = [];
const btn = document.getElementById('rec');
const status = document.getElementById('status');

btn.onmousedown = btn.ontouchstart = async () => {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  chunks = [];
  mediaRecorder.ondataavailable = e => chunks.push(e.data);
  mediaRecorder.start();
  status.textContent = "Recording...";
};

btn.onmouseup = btn.ontouchend = () => {
  mediaRecorder.stop();
  status.textContent = "Sending...";
  mediaRecorder.onstop = async () => {
    const blob = new Blob(chunks, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append('audio', blob, 'clip.webm');

    const response = await fetch('/talk', { method: 'POST', body: formData });
    const audioBlob = await response.blob();
    document.getElementById('player').src = URL.createObjectURL(audioBlob);
    status.textContent = "Done.";
  };
};
</script>
</body></html>
"""

@app.route("/")
def homepage():
    return render_template_string(PAGE)


# ---------- the actual pipeline ----------
@app.route("/talk", methods=["POST"])
def talk():
    if "audio" not in request.files:
        return {"error": "no audio file received"}, 400

    audio_file = request.files["audio"]
    request_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{request_id}_{audio_file.filename}")
    audio_file.save(input_path)

    # ---- STEP 1: transcribe ----
    segments, info = whisper_model.transcribe(input_path, beam_size=5)
    heard_text = " ".join(seg.text for seg in segments).strip()
    print(f"[talk] heard: {heard_text!r} (lang={info.language})")

    # ---- STEP 2: parse (placeholder — just acknowledging what we heard for now) ----

    # ---- STEP 3: Check for commands
    clean_text = heard_text.lower().strip().translate(str.maketrans('', '', string.punctuation))
    command = clean_text.split()[0]
    
    match command.lower():
        case "parrot" | "papagailis" | "попугай":
            reply_text = heard_text.split(command,1)[1]
        case "die":
            reply_text = "Goodbye!"
        case _:
            match info.language:
                case "en":
                    reply_text = f"There is no such command!"
                case "lv":
                    reply_text = f"Nav tādas komandas!"
                case "ru":
                    reply_text = f"Нет такой команды!"
                case _:
                    reply_text = f"There is no such command!"

    # ---- STEP 4: generate spoken reply ----
    voice(reply_text, info.language)

    # ---- STEP 5s: send the reply audio back ----
    output_path = "output.wav"  # or your request_id path

    return send_file(
        output_path,
        mimetype="audio/wav"
    )

    # also send text    


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=55555)