"""
speaker.py
TTS output using Piper (primary) with a pyttsx3 fallback.

Piper pipeline:
  text  ──►  piper.exe --output_file temp.wav  ──►  sounddevice playback

If piper.exe is not found at the configured path the module falls back to
pyttsx3 (built-in Windows SAPI voice).  If neither is available TTS is
silently disabled (text is only logged).
"""
import os
import subprocess
import tempfile
import wave

import numpy as np
import sounddevice as sd

from config.settings import PIPER_EXE, VOICE_MODEL
from core.logger import get_logger

logger = get_logger(__name__)


class Speaker:

    def __init__(self):
        self._piper_ok   = os.path.isfile(PIPER_EXE)
        self._pyttsx3    = None

        if self._piper_ok:
            logger.info("TTS: Piper found at '%s'.", PIPER_EXE)
        else:
            logger.warning("TTS: Piper not found at '%s' — trying pyttsx3.", PIPER_EXE)
            self._init_pyttsx3()

    # ── Availability ──────────────────────────────────────────────────────────
    def _init_pyttsx3(self):
        try:
            import pyttsx3
            self._pyttsx3 = pyttsx3.init()
            # Optional: slow down rate slightly for clarity
            rate = self._pyttsx3.getProperty("rate")
            self._pyttsx3.setProperty("rate", max(120, rate - 20))
            logger.info("TTS: pyttsx3 fallback ready.")
        except Exception as e:
            logger.warning("TTS: pyttsx3 unavailable (%s). TTS disabled.", e)

    # ── Public API ────────────────────────────────────────────────────────────
    def speak(self, text: str):
        """Synthesise and play `text` using the best available engine."""
        text = (text or "").strip()
        if not text:
            return

        if self._piper_ok:
            self._speak_piper(text)
        elif self._pyttsx3 is not None:
            self._speak_pyttsx3(text)
        else:
            logger.info("[TTS disabled] %s", text)

    # ── Piper ─────────────────────────────────────────────────────────────────
    def _speak_piper(self, text: str):
        tmp_wav = tempfile.mktemp(suffix=".wav")
        try:
            result = subprocess.run(
                [PIPER_EXE, "--model", VOICE_MODEL, "--output_file", tmp_wav],
                input=text,
                text=True,
                capture_output=True,
                timeout=30,
            )
            if result.returncode != 0:
                logger.error("Piper exited %d: %s",
                             result.returncode, result.stderr.strip())
                return
            self._play_wav(tmp_wav)
        except subprocess.TimeoutExpired:
            logger.error("Piper timed out for text: '%s'…", text[:40])
        except Exception as e:
            logger.error("Piper speak error: %s", e)
        finally:
            try:
                os.remove(tmp_wav)
            except OSError:
                pass

    @staticmethod
    def _play_wav(path: str):
        """Read a WAV file and play it through sounddevice."""
        try:
            with wave.open(path, "rb") as wf:
                rate   = wf.getframerate()
                frames = wf.readframes(wf.getnframes())

            # Convert int16 PCM → float32 in [-1, 1]
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            sd.play(audio, samplerate=rate)
            sd.wait()
        except Exception as e:
            logger.error("WAV playback error: %s", e)

    # ── pyttsx3 fallback ──────────────────────────────────────────────────────
    def _speak_pyttsx3(self, text: str):
        try:
            self._pyttsx3.say(text)
            self._pyttsx3.runAndWait()
        except Exception as e:
            logger.error("pyttsx3 speak error: %s", e)