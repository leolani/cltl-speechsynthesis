from google.cloud import texttospeech
from typing import Optional

from leolani.speech_synthesis.abstract.text_to_speech import AbstractTextToSpeech


class WavenetAPITextToSpeech(AbstractTextToSpeech):
    """
    System Text to Speech

    Parameters
    ----------
    language: str
        `Language Code <https://cloud.google.com/speech/docs/languages>`_
    """
    GENDER = 2  # "Female" or 1 "Male"
    VOICE_TYPE = "en-US-Wavenet-J"

    def __init__(self, language):
        # type: (str) -> None
        AbstractTextToSpeech.__init__(self, language)

        self._client = texttospeech.TextToSpeechClient()
        self._voice = texttospeech.VoiceSelectionParams(language_code=language, name=self.VOICE_TYPE,
                                                        ssml_gender=self.GENDER)

        # Select the type of audio file you want returned
        self._audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16)

        self._log.debug("Booted (text -> speech)")

    def on_text_to_speech(self, text, animation=None):
        # type: (str, Optional[str]) -> None
        """
        Say something through Text to Speech

        Parameters
        ----------
        text: str
        animation: str
        """
        file = None

        for i in range(3):
            try:
                synthesis_input = texttospeech.SynthesisInput(text=text)
                response = self._client.synthesize_speech(input=synthesis_input, voice=self._voice,
                                                          audio_config=self._audio_config)
                file = self._create_audio(response.audio_content)
                break

            except:
                self._log.exception("Couldn't Synthesize Speech ({})".format(i + 1))

        if self.play_audio:
            self._play_file(file)

        if not self.save_audio:
            self._delete_file(file)
