# Alexa-like Windows Assistant (local activation + command execution)

## What it does
- Listens to your microphone.
- Waits for: **“hello alexa activated”**
- Then executes allowlisted commands:
  - “open chrome”
  - “open vs code”
  - “open youtube”
  - “open facebook”
  - “open facebook instagram” / “open instagram”
- Stops when you say: **“alexa shut down”**

## Safety
This assistant is **allowlisted**. It will not run arbitrary commands.

## Requirements
- Windows
- Python (3.10+ recommended)
- Working microphone

## Setup
Open terminal in this folder:

```bat
cd C:\Users\Asus\Desktop\alexa_like_windows_assistant
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

> If `py`/`python` is not available, install Python from Microsoft.

## Run
```bat
cd C:\Users\Asus\Desktop\alexa_like_windows_assistant
.\.venv\Scripts\activate
python main.py
```

## Voice phrases
- Activate: **hello alexa activated**
- Commands: 
  - open chrome
  - open vs code
  - open youtube
  - open facebook
  - open instagram
- Shutdown: **alexa shut down**

## Notes
- `SpeechRecognition` uses Google Web Speech by default (requires internet).

