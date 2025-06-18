import io, os, contextlib
from gtts import gTTS
# Suppress output
with open(os.devnull, 'w') as devnull, contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
    import pygame
from threading import Thread
import keyboard  # For key tracking


# Global variable to stop playback
_playing = False


def text_to_speech(text: str, lang: str = 'en'):
    """
    Converts text to speech and plays it.
    Can be stopped by calling stop_sound().
    """
    global _playing

    try:
        # Generate audio in memory
        tts = gTTS(text=text, lang=lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)

        # Initialize Pygame and load the audio from memory
        pygame.mixer.init()
        pygame.mixer.music.load(fp)
        pygame.mixer.music.play()

        _playing = True

        # Wait for playback to finish or to be stopped
        while pygame.mixer.music.get_busy() and _playing:
            continue

        pygame.mixer.quit()

    except Exception as e:
        print(f"Error during speech synthesis: {e}")
    finally:
        _playing = False


def text_to_speech_withEsc(text: str, lang: str = 'en'):
    """
    Converts text to speech and plays it.
    Playback can be stopped by pressing Esc.
    """
    try:
        # Generate audio in memory
        tts = gTTS(text=text, lang=lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)

        # Initialize Pygame and load the audio from memory
        pygame.mixer.init()
        pygame.mixer.music.load(fp)
        pygame.mixer.music.play()

        # Play until finished or Esc is pressed
        while pygame.mixer.music.get_busy():
            if keyboard.is_pressed('esc'):
                pygame.mixer.music.stop()
                print("Playback stopped (Esc)")
                break

        pygame.mixer.quit()

    except Exception as e:
        print(f"Error during speech synthesis: {e}")
    finally:
        pass


def speak_async(text: str, lang: str = 'ru'):
    """Plays speech asynchronously in a separate thread"""
    Thread(target=text_to_speech, args=(text, lang), daemon=True).start()


def stop_sound():
    """Stops current playback"""
    global _playing
    if _playing:
        pygame.mixer.music.stop()
        _playing = False
        print("Playback stopped")


def listen_for_stop_key():
    """Starts listening for the Esc key to stop playback"""
    def key_listener():
        keyboard.wait('esc')  # Waits for Esc key press
        stop_sound()

    Thread(target=key_listener, daemon=True).start()