import os
from pathlib import Path
from typing import Optional

from google.cloud import texttospeech

from cltl.speech_synthesis.api import SpeechSynthesisInput, SpeechSynthesisOutput
from cltl.speech_synthesis.implementation import SpeechSynthesisAbstractComponent


class WavenetAPITextToSpeech(SpeechSynthesisAbstractComponent):
    """
    System Text to Speech

    Parameters
    ----------
    language: str
        `Language Code <https://cloud.google.com/speech/docs/languages>`_
    """
    GENDER = 2  # "Female" or 1 "Male"
    VOICE_TYPE = "en-US-Wavenet-H"

    def __init__(self, language: str, play_audio: Optional[bool] = True, save_audio: Optional[bool] = True,
                 audios_dir: Optional[Path] = None) -> None:
        SpeechSynthesisAbstractComponent.__init__(self, language, play_audio, save_audio, audios_dir)

        # TODO Get rid of the need for the root_dir
        root_dir = Path(__file__).parents[3]
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(root_dir / "config" / "google_cloud_key.json")

        self._client = texttospeech.TextToSpeechClient()
        self._voice = texttospeech.VoiceSelectionParams(language_code=language, name=self.VOICE_TYPE,
                                                        ssml_gender=self.GENDER)

        # Select the type of audio file you want returned
        self._audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16)

        self._log.debug("Booted (text -> speech)")

    def text_to_speech(self, text: SpeechSynthesisInput, audio_file_prefix: str = '') -> SpeechSynthesisOutput:
        """
        Say something through Text to Speech

        Parameters
        ----------
        text: str
        audio_file_prefix: str
        """
        file = None

        for i in range(3):
            try:
                synthesis_input = texttospeech.SynthesisInput(text=text)
                response = self._client.synthesize_speech(input=synthesis_input, voice=self._voice,
                                                          audio_config=self._audio_config)
                file = self._create_audio(response.audio_content, audio_file_prefix=audio_file_prefix)
                break

            except:
                self._log.exception("Couldn't Synthesize Speech ({})".format(i + 1))

        if self.play_audio:
            self._play_file(file)

        if not self.save_audio:
            self._delete_file(file)
            return None
        else:
            return str(file)
