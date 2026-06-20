import os
import sys
import time
import webbrowser
import subprocess
import threading
import re

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None


ACTIVATE_PHRASES = [
    "hello alexa activated",
    "alexa activated",
    "hello alexa",
]

SHUTDOWN_PHRASES = [
    "alexa shut down",
    "alexa shutdown",
    "shut down",
    "stop listening",
]

# Allowlisted actions (safe by design: only open known URLs/apps)
ALLOWLIST = {
    "open chrome": {
        "type": "app",
        "value": "chrome",
    },
    "open vs code": {
        "type": "app",
        "value": "code",
    },
    "open youtube": {
        "type": "url",
        "value": "https://www.youtube.com/",
    },
    "open facebook instagram": {
        "type": "url",
        "value": "https://www.instagram.com/",
    },
    "open instagram": {
        "type": "url",
        "value": "https://www.instagram.com/",
    },
    "open facebook": {
        "type": "url",
        "value": "https://www.facebook.com/",
    },
}


def norm_text(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s


def tts_speak(text: str):
    if pyttsx3 is None:
        print(text)
        return

    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    engine.setProperty("volume", 1.0)
    engine.say(text)
    engine.runAndWait()


def open_app(app_name: str):
    # Best-effort: rely on PATH or common locations.
    # Chrome: 'chrome' usually works to open default browser; fallback to web.
    app_name_lower = app_name.lower()

    if app_name_lower in ("chrome", "google chrome"):
        tts_speak("Opening Chrome")
        try:
            # Try Windows default Chrome via start
            subprocess.Popen(["cmd", "/c", "start", "" ,"chrome"], shell=False)
        except Exception:
            webbrowser.open("https://www.google.com")
        return

    if app_name_lower in ("code", "vscode", "visual studio code"):
        tts_speak("Opening VS Code")
        # Try to call 'code' command (installed with VS Code launcher)
        try:
            subprocess.Popen(["cmd", "/c", "start", "", "code"], shell=False)
        except Exception:
            # Fallback to default VS Code install path (may vary)
            candidates = [
                r"C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
                r"C:\\Program Files\\Microsoft VS Code\\Code.exe",
                r"C:\\Program Files\\Microsoft VS Code\\bin\\code.cmd",
            ]
            for c in candidates:
                c2 = c.replace("%USERNAME%", os.environ.get("USERNAME", ""))
                if os.path.exists(c2):
                    subprocess.Popen([c2], shell=False)
                    return
            # Last resort
            webbrowser.open("https://code.visualstudio.com/")
        return

    raise ValueError(f"Unknown app allowlist target: {app_name}")


def handle_command(cmd: str):
    cmd_n = norm_text(cmd)

    # Find the best matching allowlisted key by prefix/contains.
    # Example: user says "open vs code" exact.
    # Also allow slight variations.
    for key, action in ALLOWLIST.items():
        if cmd_n == key:
            if action["type"] == "url":
                url = action["value"]
                tts_speak(f"Opening {url}")
                webbrowser.open(url)
                return
            if action["type"] == "app":
                open_app(action["value"])
                return

    # Some fuzzy handling for user phrasing
    if "open" in cmd_n and "chrome" in cmd_n:
        open_app("chrome")
        return
    if "open" in cmd_n and ("vs" in cmd_n and "code" in cmd_n or "vscode" in cmd_n):
        open_app("code")
        return
    if "open" in cmd_n and "youtube" in cmd_n:
        webbrowser.open("https://www.youtube.com/")
        tts_speak("Opening YouTube")
        return
    if "open" in cmd_n and "instagram" in cmd_n:
        webbrowser.open("https://www.instagram.com/")
        tts_speak("Opening Instagram")
        return

    tts_speak("Sorry, I do not recognize that command.")


def listen_loop():
    if sr is None:
        tts_speak("Speech recognition library not installed. Run pip install -r requirements.txt")
        return

    recognizer = sr.Recognizer()
    # Adjust for noisy environments
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8

    mic = None
    try:
        mic = sr.Microphone()
    except Exception as e:
        # Common issue on Windows: PyAudio / audio backend not configured.
        # Fall back to console input so the assistant is still usable.
        tts_speak("Microphone not available. Type commands in the console instead.")
        print(f"Microphone init error: {e}")


    active = False
    tts_speak("Alexa assistant ready. Say 'hello alexa activated' to start.")

    active = False
    tts_speak("Alexa assistant ready. Say 'hello alexa activated' to start.")

    if mic is None:
        # Console fallback loop (so the app is still usable even without PyAudio/mic)
        while True:
            try:
                text = input("> ")
            except KeyboardInterrupt:
                tts_speak("Stopped")
                break

            text_n = norm_text(text)
            if not active:
                if any(text_n == norm_text(p) or norm_text(p) in text_n for p in ACTIVATE_PHRASES):
                    active = True
                    tts_speak("Activated. What do you want?")
                continue

            if any(text_n == norm_text(p) or norm_text(p) in text_n for p in SHUTDOWN_PHRASES):
                active = False
                tts_speak("Shutting down. Bye")
                continue

            handle_command(text_n)

    while True:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.6)
            audio = recognizer.listen(source, timeout=None)


        try:
            text = recognizer.recognize_google(audio)
            text_n = norm_text(text)
            print(f"You said: {text}")

            if not active:
                if any(text_n == norm_text(p) or norm_text(p) in text_n for p in ACTIVATE_PHRASES):
                    active = True
                    tts_speak("Activated. What do you want?")
                else:
                    # ignore while idle
                    continue
            else:
                if any(text_n == norm_text(p) or norm_text(p) in text_n for p in SHUTDOWN_PHRASES):
                    active = False
                    tts_speak("Shutting down. Bye")
                    continue

                handle_command(text_n)

        except sr.UnknownValueError:
            if active:
                tts_speak("I did not catch that.")
        except sr.RequestError:
            tts_speak("Speech recognition failed (network error).")
        except KeyboardInterrupt:
            tts_speak("Stopped")
            break


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    listen_loop()


if __name__ == "__main__":
    main()

