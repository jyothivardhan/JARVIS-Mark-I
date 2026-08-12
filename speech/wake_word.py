"""
wake_word.py
Whisper-based wake-word detector.

Records short audio clips (WAKE_LISTEN_DURATION seconds) in a loop,
transcribes each clip with the shared WhisperModel, and checks whether
the transcription contains the configured WAKE_WORD.

The WhisperModel instance is shared with the Listener to avoid loading
the model twice.
"""
import os
import wave
import tempfile

import numpy as np
import sounddevice as sd

from config.settings import SAMPLE_RATE, WAKE_WORD, WAKE_LISTEN_DURATION
from core.logger import get_logger

logger = get_logger(__name__)

_CLIP_FRAMES = int(SAMPLE_RATE * WAKE_LISTEN_DURATION)


class WakeWordDetector:
    """
    Continuously polls the microphone for the wake word.

    Args:
        whisper_model: A loaded `faster_whisper.WhisperModel` instance
                       (shared from `Listener` to avoid double-loading).
        wake_word: Override the default WAKE_WORD from settings.
    """

    def __init__(self, whisper_model, wake_word: str = WAKE_WORD):
        self._model     = whisper_model
        self._wake_word = wake_word.lower().strip()

    # ── Recording ─────────────────────────────────────────────────────────────
    def _record_clip(self) -> str:
        """Record a short clip and return the path to a temp WAV file."""
        tmp = tempfile.mktemp(suffix=".wav")
        try:
            audio = sd.rec(
                _CLIP_FRAMES,
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
            )
            sd.wait()
            self._save_wav(audio.flatten(), tmp)
        except Exception as e:
            logger.warning("Wake-word clip recording failed: %s", e)
        return tmp

    @staticmethod
    def _save_wav(audio: np.ndarray, path: str):
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio.tobytes())

    # ── Transcription ─────────────────────────────────────────────────────────
    def _transcribe(self, path: str) -> str:
        try:
            segments, _ = self._model.transcribe(path, language="en")
            text = " ".join(seg.text for seg in segments).strip().lower()
            return text
        except Exception as e:
            logger.debug("Wake-word transcription error: %s", e)
            return ""
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

    # ── Main loop ─────────────────────────────────────────────────────────────
    def listen(self) -> bool:
        """
        Block until the wake word is heard.
        Returns True when the wake word is detected.
        """
        logger.info("Wake-word detector active. Say '%s'…", self._wake_word)
        print(f"\n[Wake word] Waiting for '{self._wake_word}'…", flush=True)

        while True:
            clip_path = self._record_clip()
            text      = self._transcribe(clip_path)

            if text:
                logger.debug("Wake-word clip transcribed: '%s'", text)

            if self._wake_word in text:
                logger.info("Wake word '%s' detected!", self._wake_word)
                print(f"[Wake word detected] Listening for your command…", flush=True)
                return True
