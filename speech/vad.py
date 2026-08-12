"""
vad.py
Energy-based Voice Activity Detection (VAD).

Streams audio from the default microphone in ~30 ms chunks.
Recording starts immediately and stops when:
  • VAD_SILENCE_TIMEOUT seconds of consecutive silence follow detected speech, OR
  • VAD_MAX_DURATION seconds have elapsed (hard cap).

No external C libraries required — uses only sounddevice + numpy.
"""
import wave
import os
import numpy as np
import sounddevice as sd

from config.settings import (
    SAMPLE_RATE,
    VAD_SILENCE_THRESHOLD,
    VAD_SILENCE_TIMEOUT,
    VAD_MAX_DURATION,
    VAD_CHUNK_DURATION,
)
from core.logger import get_logger

logger = get_logger(__name__)

_CHUNK_FRAMES = int(SAMPLE_RATE * VAD_CHUNK_DURATION)


def _rms(chunk: np.ndarray) -> float:
    """Root-Mean-Square energy of an int16 audio chunk."""
    return float(np.sqrt(np.mean(chunk.astype(np.float64) ** 2)))


class VAD:
    """
    VAD-gated microphone recorder.

    Usage:
        vad = VAD()
        wav_path = vad.record_until_silence()   # blocks until done
    """

    def __init__(
        self,
        threshold: float = VAD_SILENCE_THRESHOLD,
        silence_timeout: float = VAD_SILENCE_TIMEOUT,
        max_duration: float = VAD_MAX_DURATION,
        sample_rate: int = SAMPLE_RATE,
    ):
        self.threshold       = threshold
        self.silence_timeout = silence_timeout
        self.max_duration    = max_duration
        self.sample_rate     = sample_rate

    def record_until_silence(self, filename: str = "voice.wav") -> str:
        """
        Stream the microphone, detect speech, and stop after silence.
        Saves audio to `filename` and returns its path.
        """
        max_chunks            = int(self.max_duration    / VAD_CHUNK_DURATION)
        silence_chunks_needed = int(self.silence_timeout / VAD_CHUNK_DURATION)

        frames: list[np.ndarray] = []
        speech_started = False
        silent_streak  = 0

        logger.info("VAD: recording (threshold=%d, silence=%.1fs)…",
                    self.threshold, self.silence_timeout)

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                blocksize=_CHUNK_FRAMES,
            ) as stream:
                for _ in range(max_chunks):
                    chunk, _ = stream.read(_CHUNK_FRAMES)
                    chunk = chunk.flatten()
                    energy = _rms(chunk)

                    if energy > self.threshold:
                        speech_started = True
                        silent_streak  = 0
                    else:
                        if speech_started:
                            silent_streak += 1

                    frames.append(chunk)

                    if speech_started and silent_streak >= silence_chunks_needed:
                        logger.debug("VAD: silence detected — stopping.")
                        break

        except Exception as e:
            logger.error("VAD stream error: %s", e)

        if not frames:
            # Return empty file so callers don't crash
            self._save_wav(np.zeros(1, dtype=np.int16), filename)
            return filename

        audio = np.concatenate(frames)
        self._save_wav(audio, filename)
        logger.info("VAD: saved %.2f s of audio to '%s'.",
                    len(audio) / self.sample_rate, filename)
        return filename

    @staticmethod
    def _save_wav(audio: np.ndarray, path: str):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)          # int16 = 2 bytes/sample
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio.tobytes())
