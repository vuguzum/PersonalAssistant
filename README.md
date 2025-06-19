
# 🎙️ Voice Assistant with Real-Time Speech Recognition and Response

This is a real-time voice assistant built in Python using [OpenAI Whisper](https://github.com/openai/whisper), [WebRTC Voice Activity Detection (VAD)](https://github.com/wiseman/py-webrtcvad), and a local LLM server for generating responses. The assistant listens for speech when you press the spacebar, transcribes it using Whisper, sends the transcribed text to a chatbot endpoint, and optionally speaks the response aloud using gTTS.

## 🚀 Features

- Real-time microphone input and recording
- On-device Whisper speech-to-text transcription
- Voice activity detection (VAD) for intelligent segmentation
- Chatbot response via local LLM API
- Text-to-speech response using `gTTS_module`
- Terminal theming (light/dark)
- Multithreaded design for responsive interaction

## 📦 Dependencies

Install required libraries via pip:

```bash
pip install numpy sounddevice keyboard openai-whisper torch webrtcvad requests colorama
```

> You also need a working `gTTS_module.py` in the same directory with a function:  
> `text_to_speech_withEsc(text: str)` that plays audio and exits on `Esc`.

## 🛠️ Usage

1. **Run the script**:
   ```bash
   python pers_assist.py
   ```

2. **Press the `Space` key** to toggle voice recording.

3. **Speak** into your microphone. When you stop talking, the assistant transcribes your speech and responds.

4. The assistant **prints the response** in the terminal and **speaks it aloud**.

## 📡 LLM Chatbot Backend

You can use this assistant with a local language model by installing [LM Studio](https://lmstudio.ai), which provides an easy interface for running models locally.

For example, you can load and serve the model [`google/gemma-3-4b`] in LM Studio.

Make sure LM Studio is configured to serve an OpenAI-compatible API at:

```
http://localhost:1234/v1/chat/completions
```

The request format sent is:

This assistant expects a local language model server running at:

```
http://localhost:1234/v1/chat/completions
```

The request format sent is:
```json
{
  "messages": [{"role": "user", "content": "your question"}]
}
```

Make sure your backend server supports this structure (e.g. OpenAI-compatible).

## 🧠 Model Selection

Whisper models supported:
- `tiny`, `base`, `small`, `medium`, `large`, etc.
- `.en` suffix for English-only variants

By default, it uses the `"medium"` model and chooses `cuda` if available, otherwise `cpu`.

## 🎨 Themes

Two terminal color themes are available:
- `"light"` (default)
- `"dark"`

You can switch by changing:
```python
THEME = THEMES["light"]
```

## 📝 Notes

- Pressing the spacebar toggles recording on/off.
- The assistant detects silence to trigger transcription and response generation.
- VAD settings are tuned for responsiveness and low false positives.

## 📄 License

General Public License. See `LICENSE` file for details.



