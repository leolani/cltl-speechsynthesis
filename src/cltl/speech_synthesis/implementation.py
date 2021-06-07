import wave
from datetime import datetime
from pathlib import Path
from typing import Optional

import pyaudio

from cltl.speech_synthesis.api import SpeechSynthesisComponent


class SpeechSynthesisAbstractComponent(SpeechSynthesisComponent):
    """
    System Text to Speech

    Parameters
    ----------
    language: str
    """

    def __init__(self, language: str, play_audio: Optional[bool] = True, save_audio: Optional[bool] = True,
                 audios_dir: Optional[Path] = None) -> None:
        SpeechSynthesisComponent.__init__(self, language, play_audio, save_audio, audios_dir)

    def set_audio_path(self, audios_dir):
        self.audios_dir = Path(audios_dir)
        self.audios_dir.mkdir(parents=True, exist_ok=True)

    def create_filename(self, prefix=''):
        if prefix == '':
            prefix = datetime.now().strftiøme('%Y-%m-%d-%H-%M')

        name = "{}_{}.wav".format(prefix, self.__class__.__name__)

        return self.audios_dir / name

    def _create_audio(self, mp3, audio_file_prefix=''):
        file = self.create_filename(prefix=audio_file_prefix)
        try:
            with open(file, 'wb') as wav_file:
                wav_file.write(mp3)

            self._log.debug("Audio content written to file '{}'".format(file))

        except:
            self._log.exception("Failed to write temporary file")

        return file

    def _play_file(self, file):
        if not file:
            return

        try:
            with wave.open(str(file), 'rb') as wav_file:
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
        if file and Path.exists(file):
            Path.unlink(file)
