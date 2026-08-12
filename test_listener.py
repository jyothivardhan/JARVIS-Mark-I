from speech.listener import Listener

listener = Listener()

text = listener.transcribe("voice.wav")

print()
print("Recognized:")
print(text) 