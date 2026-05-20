from dataclasses import dataclass


@dataclass
class TranscriptionResult:
    transcript: str
    confidence: float
    duration_seconds: float | None = None


class WhisperTranscriptionService:
    """Boundary for a Whisper-compatible transcription provider."""

    def __init__(self, model_name: str = "large-v3") -> None:
        self.model_name = model_name

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        raise NotImplementedError(
            "Wire this boundary to local Whisper, OpenAI audio transcription, or a managed speech service."
        )
