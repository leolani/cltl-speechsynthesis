import wave

import logging
import os
import pyaudio
from datetime import datetime
from typing import Optional, Union

logger = logging.getLogger(__name__)


class AbstractTextToSpeech(object):
    """
    Abstract Text To Speech

    Parameters
    ----------
    language: str
        `Language Code <https://cloud.google.com/speech/docs/languages>`_

    save_audio: bool
    play_audio: bool
    """
    _AUDIO_FILE_BUFFER_SIZE = 1024

    def __init__(self, language, play_audio=True, save_audio=True):
        # type: (str) -> None
        self._log = logger.getChild(self.__class__.__name__)

        self._language = language
        self.play_audio = play_audio
        self.save_audio = save_audio
        self._talking_jobs = 0

        self.audios_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../..'))

    @property
    def language(self):
        # type: () -> str
        """
        `Language Code <https://cloud.google.com/speech/docs/languages>`_

        Returns
        -------
        language: str
            `Language Code <https://cloud.google.com/speech/docs/languages>`_
        """
        return self._language

    @property
    def talking(self):
        # type: () -> bool
        """
        Returns whether system is currently producing speech

        Returns
        -------
        talking: bool
            Whether system is currently producing speech
        """
        return self._talking_jobs >= 1

    def on_text_to_speech(self, text, animation=None):
        # type: (Union[str, unicode], Optional[str]) -> None
        """
        Say something through Text to Speech (Implementation)

        Text To Speech Backends should implement this function
        This function should block while speech is being produced

        Parameters
        ----------
        text: str
        animation: str
        """
        raise NotImplementedError()

    def create_filename(self):
        return os.path.join(self.audios_dir, "audios/{}_{}.wav".format(self.__class__.__name__,
                                                                                datetime.now().strftime(
                                                                                    '%Y-%m-%d-%H-%M')))

    def _create_audio(self, mp3):
        file = self.create_filename()
        try:
            with open(file, 'wb') as wav_file:
                wav_file.write(mp3)

            self._log.debug("Audio content written to file '{}'".format(file))

        except:
            self._log.exception("Failed to write temporary file")

        return file

    def _play_file(self, file):

        try:
            with wave.open(file, 'rb') as wav_file:
                width = wav_file.getsampwidth()
                channels = wav_file.getnchannels()
                rate = wav_file.getframerate()
                pa = pyaudio.PyAudio()
                pa_stream = pa.open(format=pyaudio.get_format_from_width(width),
                                    channels=channels,
                                    rate=rate,
                                    output=True)

                data = wav_file.readframes(self._AUDIO_FILE_BUFFER_SIZE)

                # play stream (looping from beginning of file to the end)
                while data != b'' and data != '':
                    # writing to the stream is what *actually* plays the sound.
                    pa_stream.write(data)
                    data = wav_file.readframes(self._AUDIO_FILE_BUFFER_SIZE)

                # cleanup stuff.
                pa_stream.close()
                pa.terminate()
        except:
            self._log.exception("Failed to play wav file")


    @staticmethod
    def _delete_file(file):
        if file and os.path.exists(file.name):
            os.remove(file.name)
