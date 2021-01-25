import os
import tempfile
import wave

import commons
from WaveRNN import models
import numpy as np
import torch
import utils
from text import text_to_sequence, cmudict
from text.symbols import symbols

from inference_e2e import main

from leolani.speech_synthesis.abstract.text_to_speech import AbstractTextToSpeech

_AUDIO_FILE_BUFFER_SIZE = 1024


class GlowTextToSpeech(AbstractTextToSpeech):
    """
    System Text to Speech

    Parameters
    ----------
    language: str
        `Language Code `_
    """
    GENDER = 2  # "Female" or 1 "Male"
    VOICE_TYPE = "en-US-Wavenet-J"

    def __init__(self, language):
        # type: (str) -> None
        AbstractTextToSpeech.__init__(self, language)

        self._log.debug("Booted (text -> speech)")

        self.hps, self.model, self.cmu_dict = self.initialize()
        self.x_tst, self.x_tst_lengths = self.prep_inference()
        self.generate_mel()

    def initialize(self):
        # If you are using a provided pretrained model
        hps = utils.get_hparams_from_file("./configs/base_blank.json")
        checkpoint_path = "./glow_blank.pth"

        model = models.FlowGenerator(
            len(symbols) + getattr(hps.data, "add_blank", False),
            out_channels=hps.data.n_mel_channels,
            **hps.model).to("cuda")

        utils.load_checkpoint(checkpoint_path, model)
        model.decoder.store_inverse()  # do not calcuate jacobians for fast decoding
        _ = model.eval()

        cmu_dict = cmudict.CMUDict(hps.data.cmudict_path)

        return hps, model, cmu_dict

    def prep_inference(self):
        tst_stn = "Glow TTS is really awesome !"

        if getattr(self.hps.data, "add_blank", False):
            text_norm = text_to_sequence(tst_stn.strip(), ['english_cleaners'], self.cmu_dict)
            text_norm = commons.intersperse(text_norm, len(symbols))
        else:  # If not using "add_blank" option during training, adding spaces at the beginning and the end of utterance improves quality
            tst_stn = " " + tst_stn.strip() + " "
            text_norm = text_to_sequence(tst_stn.strip(), ['english_cleaners'], self.cmu_dict)
        sequence = np.array(text_norm)[None, :]
        print("".join([symbols[c] if c < len(symbols) else "<BNK>" for c in sequence[0]]))
        x_tst = torch.autograd.Variable(torch.from_numpy(sequence)).cuda().long()
        x_tst_lengths = torch.tensor([x_tst.shape[1]]).cuda()

        return x_tst, x_tst_lengths

    def generate_mel(self):
        with torch.no_grad():
            noise_scale = .667
            length_scale = 1.0
            (y_gen_tst, *_), *_, (attn_gen, *_) = self.model(self.x_tst, self.x_tst_lengths, gen=True,
                                                             noise_scale=noise_scale,
                                                             length_scale=length_scale)

        # save mel-frames
        if not os.path.exists('./hifi-gan/test_mel_files'):
            os.makedirs('./hifi-gan/test_mel_files')
        np.save("./hifi-gan/test_mel_files/sample.npy", y_gen_tst.cpu().detach().numpy())

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
                synthesis_input = main()
                # file = self._create_sound(response.audio_content)

                # if play_file:
                #     self._play_file(file.name)
                # 
                # if not save_file:
                #     self._delete_file(file)

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
