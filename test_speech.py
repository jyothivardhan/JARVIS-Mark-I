from speech.speech_manager import SpeechManager

speech = SpeechManager()

print("\nSpeak now...\n")

text = speech.listen()

print("\nRecognized:")
print(text)