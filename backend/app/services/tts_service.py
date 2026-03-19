"""Text-to-Speech service using Google Cloud TTS."""

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TTSService:
    """
    Text-to-Speech via Google Cloud Text-to-Speech.
    Falls back to empty bytes when credentials unavailable.
    """

    def __init__(self) -> None:
        self.voice_name = settings.tts_voice_name
        self.language_code = settings.tts_language_code
        self._client = None

    def _get_client(self):
        """Lazy init TTS client."""
        if self._client is None:
            try:
                from google.cloud import texttospeech
                self._client = texttospeech.TextToSpeechClient()
            except Exception as e:
                logger.debug("Google Cloud TTS not available: %s", e)
        return self._client

    def synthesize(self, text: str) -> bytes:
        """Convert text to audio. Returns MP3 bytes."""
        client = self._get_client()
        if not client or not text.strip():
            return b""

        try:
            from google.cloud import texttospeech
            voice = texttospeech.VoiceSelectionParams(
                language_code=self.language_code,
                name=self.voice_name,
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,
            )
            response = client.synthesize_speech(
                input=texttospeech.SynthesisInput(text=text),
                voice=voice,
                audio_config=audio_config,
            )
            return response.audio_content
        except Exception as e:
            logger.warning("TTS synthesis failed: %s", e)
            return b""
