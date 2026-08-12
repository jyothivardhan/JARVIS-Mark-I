# ─── JARVIS Mark-I  ·  Global Configuration ─────────────────────────────────

ASSISTANT_NAME = "JARVIS"
VERSION = "0.3"

# ── LLM ──────────────────────────────────────────────────────────────────────
MODEL = "qwen3:4b"
MAX_HISTORY = 10        # conversation turns to keep (each turn = user + assistant)

# ── Speech / Audio ────────────────────────────────────────────────────────────
SAMPLE_RATE = 16000             # Hz — must match Whisper expectations
WHISPER_MODEL_SIZE = "base"     # tiny | base | small | medium | large

# ── Wake Word ─────────────────────────────────────────────────────────────────
WAKE_WORD = "jarvis"            # lower-case keyword Whisper must detect
WAKE_LISTEN_DURATION = 2.0      # seconds to record per wake-word check clip

# ── VAD (Voice Activity Detection) ───────────────────────────────────────────
VAD_SILENCE_THRESHOLD = 500     # RMS energy below this = silence
VAD_SILENCE_TIMEOUT   = 1.5     # seconds of silence before stopping recording
VAD_MAX_DURATION      = 15.0    # hard cap (seconds) for a single utterance
VAD_CHUNK_DURATION    = 0.03    # duration (s) of each streaming chunk (~30 ms)

# ── TTS Engine ────────────────────────────────────────────────────────────────
TTS_ENGINE  = "piper"                           # "piper" | "pyttsx3" | "none"
PIPER_EXE   = "bin/piper/piper.exe"
VOICE_MODEL = "voices/en_US-lessac-medium.onnx"

# ── Memory ────────────────────────────────────────────────────────────────────
MEMORY_FILE           = "memory/user_memory.json"
VECTOR_MEMORY_FILE    = "memory/vector_store.json"
VECTOR_EMBEDDING_MODEL = "all-MiniLM-L6-v2"    # sentence-transformers model
VECTOR_TOP_K          = 3                       # max semantic results per query

# ── UI / HUD ──────────────────────────────────────────────────────────────────
UI_ENABLED      = True  # set False to disable the Rich HUD
HUD_REFRESH_RATE = 4    # frames per second