import numpy as np
import sounddevice as sd
import keyboard
import whisper
import threading
import time
import torch
import webrtcvad
import requests
from colorama import Fore, Style, init
import re
import gTTS_module


# Initialize colorama for terminal colors
init(autoreset=True)

# === Color themes ===
THEMES = {
    "light": {  
        "user": Fore.BLUE,
        "assistant": Fore.LIGHTBLACK_EX,
        "thinking": Fore.MAGENTA,
        "background": Style.BRIGHT,
        "prompt": "Light"
    },
    "dark": {
        "user": Fore.CYAN,
        "assistant": Fore.LIGHTGREEN_EX,
        "thinking": Fore.YELLOW,
        "background": Style.DIM,
        "prompt": "Dark"
    }
}

THEME = THEMES["light"]
# print(f"\n✅ {THEME['prompt']} theme is active\n")

# --- Settings ---
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = np.int16

SEGMENT_DURATION = 0.02  # 20 ms for VAD
SEGMENT_SAMPLES = int(SAMPLE_RATE * SEGMENT_DURATION)

MIN_SPEECH_CHUNKS = 10     # minimum consecutive voice segments
SILENCE_TIMEOUT = 1.5      # seconds to wait before new line

# ['tiny.en', 'tiny', 'base.en', 'base', 'small.en', 'small', 'medium.en', 'medium', 'large-v1', 'large-v2', 'large-v3', 'large', 'large-v3-turbo', 'turbo']
# --- Whisper model initialization with CUDA support ---
device = "cuda" if torch.cuda.is_available() else "cpu"
# print(f"[Device used]: {device.upper()}")
model = whisper.load_model("medium").to(device)  # You can also specify device: whisper.load_model("small", device="cpu")

# --- VAD initialization ---
vad = webrtcvad.Vad()
vad.set_mode(3)  # sensitivity 0 - high, 3 - low

def is_speech(frame_bytes):
    try:
        return vad.is_speech(frame_bytes, SAMPLE_RATE)
    except:
        return False

# --- Global variables ---
recording = False
audio_buffer = []
buffer_index = 0
lock = threading.Lock()
last_speech_time = None

# --- Recording callback ---
def callback(indata, frames, time, status):
    if recording:
        with lock:
            audio_buffer.extend(indata.copy().flatten())

# --- Audio recording control ---
def record_audio():
    global recording
    print("Press Space to start recording...")
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE, callback=callback):
        while True:
            if keyboard.is_pressed('space'):
                toggle_recording()
                while keyboard.is_pressed('space'):
                    pass
            time.sleep(0.1)

def toggle_recording():
    global recording, audio_buffer, buffer_index
    global speech_segment, speech_started, new_line_pending, current_pause, last_speech_time

    recording = not recording
    if recording:
        print("\n[Recording started...]")
        audio_buffer.clear()
        buffer_index = 0

        # Reset VAD state
        speech_segment = []
        speech_started = False
        new_line_pending = False
        current_pause = 0.0
        last_speech_time = time.time()  # ← update start time
    else:
        print("[Recording stopped.]")

def generate_response(text):
    data = {
        "messages": [
            {"role": "user", "content": text}
        ],
        # "temperature": 0.0,        # minimal randomness
        # "max_tokens": 10,          # minimal token count
        # "stream": False,           # disable streaming
        # "stop": ["\n"]             # stop after first line
    }

    response = requests.post(
        "http://localhost:1234/v1/chat/completions",
        json=data
    )
    assist_reply = response.json()['choices'][0]['message']['content']
    # Remove tags and content between them
    # cleaned_text = re.sub(r'\<think\>.*?<\</think\>', '', assist_reply, flags=re.DOTALL)
    # print("Assistant response:", assist_reply)
    return assist_reply

# === Loading animation ===
def loading_animation(duration=1, text="Thinking"):
    symbols = ['⣷', '⣯', '⣟', '⡿', '⢿', '⣻', '⣽', '⣾']
    end_time = time.time() + duration
    idx = 0
    while time.time() < end_time:
        print(f"\r{THEME['thinking']}[{symbols[idx % len(symbols)]}] {text}{Style.RESET_ALL}", end="")
        idx += 1
        time.sleep(0.1)
    print(" " * (len(text) + 6), end="\r")  # Clear line

def process_stream():
    global last_speech_time, buffer_index
    global speech_segment, speech_started, new_line_pending, current_pause
    global recording

    while True:
        if not recording:
            time.sleep(0.5)
            continue
        question_text = ""
        with lock:
            available = len(audio_buffer)

        while buffer_index + SEGMENT_SAMPLES <= available:
            segment = audio_buffer[buffer_index:buffer_index + SEGMENT_SAMPLES]
            buffer_index += SEGMENT_SAMPLES

            segment_np = np.array(segment, dtype=np.int16)
            frame_bytes = segment_np.tobytes()

            try:
                is_silence = not is_speech(frame_bytes)

                if not is_silence:
                    speech_segment.extend(segment)
                    speech_started = True
                    new_line_pending = False
                    last_speech_time = time.time()  # ← update speech time
                elif speech_started:
                    current_pause = time.time() - last_speech_time

                    if current_pause > SILENCE_TIMEOUT:
                        if speech_segment:
                            # Transcribe and output
                            audio_float = np.array(speech_segment, dtype=np.float32) / 32768.0
                            result = model.transcribe(audio_float, language="en", verbose=None)

                            text = result["text"].strip()
                            if text.startswith("Subtitle Editor"):  # Whisper bug: reacts on noise
                                text = ""
                                continue
                            question_text += " " + text
                            if text:
                                print(f"{THEME['user']}You: {Style.RESET_ALL}{text}", end=" ", flush=True)

                            speech_segment = []

                        print()  # New line
                        speech_segment = []
                        speech_started = False
                        new_line_pending = False
                        # Generate response
                        loading_animation(text="Generating response...")
                        response = generate_response(question_text)
                        print(f"{THEME['assistant']}Assistant: {response}{Style.RESET_ALL}")
                        question_text = ""
                        recording = False
                        gTTS_module.text_to_speech_withEsc(response)
                        recording = True

            except Exception as e:
                print(f"[Error]: {e}")

        time.sleep(0.05)

# --- Entry point ---
if __name__ == "__main__":
    print("[Voice assistant application started.]")
    threading.Thread(target=record_audio, daemon=True).start()
    threading.Thread(target=process_stream, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting.")