"""
recorder.py
Fixed-duration audio recorder (fallback / testing use).
For VAD-gated recording use `speech.vad.VAD` instead.
"""
import sounddevice as sd
from scipy.io.wavfile import write

from config.settings import SAMPLE_RATE
from core.logger import get_logger

logger = get_logger(__name__)


class Recorder:
    """Records a fixed-duration audio clip and saves it as a WAV file."""

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate

    def record(self, duration: float = 5.0, filename: str = "voice.wav") -> str:
        """
        Record `duration` seconds of audio from the default microphone.

        Args:
            duration: Recording length in seconds.
            filename: Output WAV file path.

        Returns:
            Path to the saved WAV file.
        """
        logger.info("Recording %.1f s (fixed duration)…", duration)

        recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
        )
        sd.wait()
        write(filename, self.sample_rate, recording)

        logger.debug("Clip saved → %s", filename)
        return filename