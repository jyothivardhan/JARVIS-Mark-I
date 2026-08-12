from faster_whisper import WhisperModel


class Listener:

    def __init__(self, model_size="base"):

        print("Loading Whisper model...")

        self.model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8"
        )

        print("Whisper ready.")

    def transcribe(self, audio_file):

        segments, info = self.model.transcribe(audio_file)

        text = ""

        for segment in segments:
            text += segment.text + " "

        return text.strip()