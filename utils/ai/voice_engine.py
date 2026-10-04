class VoiceEngine:
    """Placeholder voice wrapper. The current app focuses on text and vision guidance."""

    def __init__(self):
        self.enabled = False

    def transcribe(self, audio_path: str) -> str:
        raise NotImplementedError("Voice transcription is not enabled in this version.")
