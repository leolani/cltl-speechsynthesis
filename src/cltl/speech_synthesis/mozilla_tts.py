from pathlib import Path
from typing import Optional

import requests

from cltl.speech_synthesis.api import SpeechSynthesisInput, SpeechSynthesisOutput
from cltl.speech_synthesis.implementation import SpeechSynthesisAbstractComponent


class MozillaTextToSpeech(SpeechSynthesisAbstractComponent):
    """
    System Text to Speech

    Parameters
    ----------
    language: str
    """

    def __init__(self, language: str, play_audio: Optional[bool] = True, save_audio: Optional[bool] = True,
                 audios_dir: Optional[Path] = None) -> None:
        SpeechSynthesisAbstractComponent.__init__(self, language, play_audio, save_audio, audios_dir)

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
                response = requests.get('http://localhost:5002/api/tts', params={'text': text})
                file = self._create_audio(response.content, audio_file_prefix=audio_file_prefix)
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
