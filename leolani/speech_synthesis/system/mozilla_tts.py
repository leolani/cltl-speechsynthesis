import requests
from typing import Optional

from leolani.speech_synthesis.abstract.text_to_speech import AbstractTextToSpeech


class MozillaTextToSpeech(AbstractTextToSpeech):
    """
    System Text to Speech

    Parameters
    ----------
    language: str
        `Language Code <https://cloud.google.com/speech/docs/languages>`_
    """

    def __init__(self, language):
        # type: (str) -> None
        AbstractTextToSpeech.__init__(self, language)

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
                response = requests.get('http://localhost:5002/api/tts', params={'text': text})
                file = self._create_audio(response.content)
                break

            except:
                self._log.exception("Couldn't Synthesize Speech ({})".format(i + 1))

        if self.play_audio:
            self._play_file(file)

        if not self.save_audio:
            self._delete_file(file)
