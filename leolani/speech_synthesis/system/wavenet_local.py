import argparse
import os
import tempfile
import wave
from os.path import expanduser
from typing import Optional

import numpy as np
import pyaudio
import pysptk
import tensorflow
from tacotron.synthesize import tacotron_synthesize

tensorflow.__version__, pysptk.__version__, np.__version__

from leolani.speech_synthesis.abstract.text_to_speech import AbstractTextToSpeech

os.chdir(expanduser("~"))
_AUDIO_FILE_BUFFER_SIZE = 1024
WAVENET_DIR = "wavenet_vocoder"
TACO2_DIR = "Tacotron-2"

wn_preset = "20180510_mixture_lj_checkpoint_step000320000_ema.json"
wn_checkpoint_path = "20180510_mixture_lj_checkpoint_step000320000_ema.pth"


class WavenetLocalTextToSpeech(AbstractTextToSpeech):
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

        self._log.debug("Booted (text -> speech)")

    def on_text_to_speech(self, text, animation=None, play_file=True, save_file=True):
        # type: (str, Optional[str], Optional[bool], Optional[bool]) -> None
        """
        Say something through Text to Speech

        Parameters
        ----------
        text: str
        animation: str
        save_file: bool
        play_file: bool
        """

        for i in range(3):
            try:
                parser = argparse.ArgumentParser()
                parser.add_argument('--checkpoint', default='logs-Tacotron/pretrained/',
                                    help='Path to model checkpoint')
                parser.add_argument('--hparams', default='symmetric_mels=False,max_abs_value=4.0,power=1.1,outputs_per_step=1',
                                    help='Hyperparameter overrides as a comma-separated list of name=value pairs')
                parser.add_argument('--model', default='Tacotron')
                parser.add_argument('--input_dir', default='training_data/',
                                    help='folder to contain inputs sentences/targets')
                parser.add_argument('--output_dir', default='output/',
                                    help='folder to contain synthesized mel spectrograms')
                parser.add_argument('--mode', default='eval',
                                    help='mode of run: can be one of (eval or synthesis)')
                parser.add_argument('--GTA', default=True,
                                    help='Ground truth aligned synthesis, defaults to True, only considered in synthesis mode')
                parser.add_argument('--text_list', default=text,
                                    help='Text file contains list of texts to be synthesized. Valid if mode=eval')
                args = parser.parse_args()

                file = tacotron_synthesize(args)

                if play_file:
                    self._play_file(file.name)

                if not save_file:
                    self._delete_file(file)

                return
            except:
                self._log.exception("Couldn't Synthesize Speech ({})".format(i + 1))

    def _create_sound(self, mp3):
        tmp_file = None
        try:
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            with tmp_file:
                tmp_file.write(mp3)

            self._log.debug("Audio content written to file '{}'".format(tmp_file.name))

        except:
            self._log.exception("Failed to write temporary file")

        return tmp_file

    @staticmethod
    def _play_file(file):
        with wave.open(file, 'rb') as wav_file:
            width = wav_file.getsampwidth()
            channels = wav_file.getnchannels()
            rate = wav_file.getframerate()
            pa = pyaudio.PyAudio()
            pa_stream = pa.open(
                format=pyaudio.get_format_from_width(width),
                channels=channels,
                rate=rate,
                output=True)

            data = wav_file.readframes(_AUDIO_FILE_BUFFER_SIZE)

            # play stream (looping from beginning of file to the end)
            while data != b'' and data != '':
                # writing to the stream is what *actually* plays the sound.
                pa_stream.write(data)
                data = wav_file.readframes(_AUDIO_FILE_BUFFER_SIZE)

            # cleanup stuff.
            pa_stream.close()
            pa.terminate()

    @staticmethod
    def _delete_file(file):
        if file and os.path.exists(file.name):
            os.remove(file.name)
