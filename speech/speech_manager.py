"""
speech_manager.py
High-level speech interface — combines VAD recorder, Whisper STT,
and wake-word detection into a single easy-to-use class.
"""
from speech.listener     import Listener
from speech.recorder     import Recorder
from speech.vad          import VAD
from speech.wake_word    import WakeWordDetector
from core.logger         import get_logger

logger = get_logger(__name__)


class SpeechManager:
    """
    Owns one instance of each speech sub-component and exposes a simple API:

      listen_for_wake_word() → bool     block until wake word heard
      listen(use_vad=True)  → str      record + transcribe one utterance
    """

    def __init__(self):
        # Load Whisper once; share the model with the wake-word detector
        self.listener      = Listener()
        self.vad           = VAD()
        self.recorder      = Recorder()          # fixed-duration fallback
        self.wake_detector = WakeWordDetector(self.listener.model)
        logger.info("SpeechManager ready.")

    # ── Wake word ─────────────────────────────────────────────────────────────
    def listen_for_wake_word(self) -> bool:
        """Block until the configured wake word is detected. Returns True."""
        return self.wake_detector.listen()

    # ── Listen & transcribe ───────────────────────────────────────────────────
    def listen(self, use_vad: bool = True) -> str:
        """
        Record one utterance and return its transcription.

        Args:
            use_vad: If True (default), use VAD-gated recording.
                     If False, fall back to a fixed 5-second recording.

        Returns:
            Transcribed text string (empty string if nothing detected).
        """
        if use_vad:
            audio_file = self.vad.record_until_silence()
        else:
            audio_file = self.recorder.record(duration=5.0)

        text = self.listener.transcribe(audio_file).strip()

        if not text:
            logger.info("SpeechManager: no speech detected.")
        else:
            logger.info("Transcribed: %s", text)

        return text