import os
import string
import uuid
import subprocess
from flask import Flask, request, send_file, render_template_string, jsonify
from faster_whisper import WhisperModel

from tts import voice

app = Flask(__name__)

# load whipser model
whisper_model = WhisperModel("small", device="cpu", compute_type="int8")

UPLOAD_DIR = "uploads"
REPLY_DIR = "replies"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPLY_DIR, exist_ok=True)


# ---------- simple test page with record button ----------
PAGE = """
<!doctype html>
<html>
<body>

<h3>Input</h3>

<label>
    <input id="sendText" type="checkbox">
    Send text instead of audio
</label>

<br><br>

<input id="textInput" placeholder="Type message..."
       style="display:none; width:300px;">

<br><br>

<button id="rec" style="width:120px;height:40px;">
    Hold to Talk
</button>

<br><br>

<h3>Output</h3>

<label>
    <input id="receiveText" type="checkbox">
    Receive text instead of audio
</label>

<p id="status"></p>
<p id="responseText"></p>

<audio id="player" autoplay></audio>

<script>
const recBtn = document.getElementById("rec");
const sendText = document.getElementById("sendText");
const receiveText = document.getElementById("receiveText");
const textInput = document.getElementById("textInput");
const status = document.getElementById("status");
const responseText = document.getElementById("responseText");
const player = document.getElementById("player");

let mediaRecorder;
let chunks = [];

// Toggle UI
sendText.onchange = () => {
    if (sendText.checked) {
        textInput.style.display = "";
        recBtn.textContent = "Send";
    } else {
        textInput.style.display = "none";
        recBtn.textContent = "Hold to Talk";
    }
};

// ---------- TEXT MODE ----------
recBtn.onclick = async () => {
    if (!sendText.checked) return;

    status.textContent = "Sending...";

    const response = await fetch("/talk", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            input_type: "text",
            output_type: receiveText.checked ? "text" : "audio",
            text: textInput.value
        })
    });

    await handleResponse(response);
};

// ---------- AUDIO MODE ----------
recBtn.onmousedown = async () => {
    if (sendText.checked) return;

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    mediaRecorder = new MediaRecorder(stream);
    chunks = [];

    mediaRecorder.ondataavailable = e => chunks.push(e.data);

    mediaRecorder.onstop = async () => {
        status.textContent = "Sending...";

        const blob = new Blob(chunks, { type: "audio/webm" });

        const formData = new FormData();
        formData.append("audio", blob, "clip.webm");
        formData.append("input_type", "audio");
        formData.append(
            "output_type",
            receiveText.checked ? "text" : "audio"
        );

        const response = await fetch("/talk", {
            method: "POST",
            body: formData
        });

        await handleResponse(response);
    };

    mediaRecorder.start();
    status.textContent = "Recording...";
};

recBtn.onmouseup = () => {
    if (!sendText.checked && mediaRecorder) {
        mediaRecorder.stop();
    }
};

// ---------- RESPONSE ----------
async function handleResponse(response) {
    if (receiveText.checked) {
        const data = await response.json();
        responseText.textContent = data.text;
        player.src = "";
    } else {
        const audioBlob = await response.blob();
        player.src = URL.createObjectURL(audioBlob);
        responseText.textContent = "";
    }

    status.textContent = "Done.";
}
</script>

</body>
</html>
"""

@app.route("/")
def homepage():
    return render_template_string(PAGE)


# ---------- the actual pipeline ----------
@app.route("/talk", methods=["POST"])
def talk():
    if request.content_type.startswith("multipart/form-data"):
        input_type = request.form.get("input_type")
        output_type = request.form.get("output_type")
        audio = request.files.get("audio")
    elif request.content_type.startswith("application/json"):
        data = request.get_json()
        input_type = data.get("input_type")
        output_type = data.get("output_type")
        text = data.get("text")

    print(input_type)
    print(output_type)

    voice_answer = 1
    if(input_type == "audio"):
        print("Audio received")
        audio_file = request.files["audio"]
        request_id = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_DIR, f"{request_id}_{audio_file.filename}")
        audio_file.save(input_path)

        # ---- STEP 1: transcribe ----
        print("Transcribing audio")
        segments, info = whisper_model.transcribe(input_path, beam_size=5)
        heard_text = " ".join(seg.text for seg in segments).strip()
        print(f"[talk] heard: {heard_text!r} (lang={info.language})")
        language = info.language

        # ---- STEP 2: Check for commands
        print("Checking audio for commands")
        clean_text = heard_text.lower().strip().translate(str.maketrans('', '', string.punctuation))
        command = clean_text.split()[0]    
    elif(input_type == "text"):
        language = "en"
        clean_text = text.lower().strip().translate(str.maketrans('', '', string.punctuation))
        command = clean_text.split()[0]
        heard_text = text


    match command.lower():
        case "parrot" | "papagailis" | "попугай":
            _,_,reply_text = heard_text.partition(" ")
        case "die":
            reply_text = "Goodbye!"
        case "send" | "aizsūti" | "отправь":
            voice_answer = 0
            _,_,reply_text = heard_text.partition(" ")
            group = ""
            group,_,reply_text = reply_text.partition(" ")
            subprocess.run([
                "curl",
                "-X", "PUT",
                "-H", "Content-Type: text/plain",
                "--data", reply_text,
                f"https://rekini.tgt.lv/{group}",
            ], check=True)
        case _:
            match language:
                case "en":
                    reply_text = f"There is no such command!"
                case "lv":
                    reply_text = f"Nav tādas komandas!"
                case "ru":
                    reply_text = f"Нет такой команды!"
                case _:
                    reply_text = f"There is no such command!"


    if(output_type == "audio"):
        if(voice_answer):
            # ---- STEP 3: generate spoken reply ----
            print("Generating spoken reply : " + reply_text)
            voice(reply_text, language)

            # ---- STEP 4: send the reply audio back ----
            print("Sending reply back")
            output_path = "output.wav"  # or your request_id path

            return send_file(
                output_path,
                mimetype="audio/wav"
            )
        return {"status":"sent"}  

    elif(output_type == "text"):
        print("sending text...")
        return jsonify({
            "text": reply_text
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=55555)