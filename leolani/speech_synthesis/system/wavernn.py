import librosa
import numpy as np
import os
import torch

from leolani.speech_synthesis.abstract.text_to_speech import AbstractTextToSpeech
from models.fatchord_version import WaveRNN
from models.tacotron import Tacotron
from utils import hparams as hp
from utils.display import simple_table
from utils.text import text_to_sequence
from utils.text.symbols import symbols


class WaveRNNTextToSpeech(AbstractTextToSpeech):
    """
    System Text to Speech

    Parameters
    ----------
    language: str
        `Language Code `_
    """

    def __init__(self, language, batched=False, force_cpu=True):
        # type: (str) -> None
        AbstractTextToSpeech.__init__(self, language)

        # Load hyperparameters
        hp_file = os.path.join(self.audios_dir, 'WaveRNN/hparams.py')
        hp.configure(hp_file)
        self.batched = batched

        # Select device to use
        self.device = self._select_device(force_cpu)

        # Initialize waveRNN
        self.voc_model = self._initialize_wavernn()
        self.voc_k = self.voc_model.get_step() // 1000

        # Initialize tacotron
        self.tts_model = self._initialize_tacotron()
        self.tts_k = self.tts_model.get_step() // 1000
        self.r = self.tts_model.r

        self._log.debug("Booted (text -> speech)")

    def _select_device(self, force_cpu):
        if not force_cpu and torch.cuda.is_available():
            device = torch.device('cuda')
        else:
            device = torch.device('cpu')
        self._log.debug('Using device:', device)

        return device

    def _initialize_wavernn(self):
        self._log.debug('Initialising WaveRNN Model')

        # Instantiate WaveRNN Model
        voc_model = WaveRNN(rnn_dims=hp.voc_rnn_dims,
                            fc_dims=hp.voc_fc_dims,
                            bits=hp.bits,
                            pad=hp.voc_pad,
                            upsample_factors=hp.voc_upsample_factors,
                            feat_dims=hp.num_mels,
                            compute_dims=hp.voc_compute_dims,
                            res_out_dims=hp.voc_res_out_dims,
                            res_blocks=hp.voc_res_blocks,
                            hop_length=hp.hop_length,
                            sample_rate=hp.sample_rate,
                            mode='MOL').to(self.device)

        voc_file = os.path.join(self.audios_dir, 'WaveRNN/pretrained/voc_weights/latest_weights.pyt')
        voc_model.load(voc_file)

        return voc_model

    def _initialize_tacotron(self):
        self._log.debug('Initialising Tacotron Model')

        # Instantiate Tacotron Model
        tts_model = Tacotron(embed_dims=hp.tts_embed_dims,
                             num_chars=len(symbols),
                             encoder_dims=hp.tts_encoder_dims,
                             decoder_dims=hp.tts_decoder_dims,
                             n_mels=hp.num_mels,
                             fft_bins=hp.num_mels,
                             postnet_dims=hp.tts_postnet_dims,
                             encoder_K=hp.tts_encoder_K,
                             lstm_dims=hp.tts_lstm_dims,
                             postnet_K=hp.tts_postnet_K,
                             num_highways=hp.tts_num_highways,
                             dropout=hp.tts_dropout,
                             stop_threshold=hp.tts_stop_threshold).to(self.device)

        tts_file = os.path.join(self.audios_dir, 'WaveRNN/pretrained/tts_weights/latest_weights.pyt')
        tts_model.load(tts_file)

        return tts_model

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
                input_text = text
                inputs = [text_to_sequence(input_text.strip(), hp.tts_cleaner_names)]

                simple_table([('WaveRNN', str(self.voc_k) + 'k'),
                              (f'Tacotron(r={self.r})', str(self.tts_k) + 'k'),
                              ('Generation Mode', 'Batched' if self.batched else 'Unbatched'),
                              ('Target Samples', 11_000 if self.batched else 'N/A'),
                              ('Overlap Samples', 550 if self.batched else 'N/A')])

                for inp, x in enumerate(inputs, 1):
                    self._log.debug(f'| Generating {inp}/{len(inputs)}')
                    file = self._create_audio(x)
                break

            except:
                self._log.exception("Couldn't Synthesize Speech ({})".format(i + 1))

        if self.play_audio:
            self._play_file(file)

        if not self.save_audio:
            self._delete_file(file)

    def _create_audio(self, x):
        tmp_file = self.create_filename()

        try:
            _, m, attention = self.tts_model.generate(x)
            m = torch.tensor(m).unsqueeze(0)
            m = (m + 4) / 8

            self.voc_model.generate(m, tmp_file, self.batched, 11_000, 550, hp.mu_law)
            self._log.debug("Audio content written to file '{}'".format(tmp_file))

            # Convert audio
            data = self.convert_audio(tmp_file)
            file = AbstractTextToSpeech._create_audio(self, data)
            self._log.debug("Converted audio content written to file '{}'".format(file))

        except:
            self._log.exception("Failed to write temporary file")

        return file if file else tmp_file

    def convert_audio(self, bad_file):
        data, sr = librosa.load(bad_file, sr=hp.sample_rate)

        dtype = np.int16
        # i = np.iinfo(dtype)
        # abs_max = 2 ** (i.bits - 1)
        # offset = i.min + abs_max
        # transformed = (data * abs_max + offset).clip(i.min, i.max).astype(dtype).tobytes()

        transformed = (data * 32767).astype(dtype)

        return transformed
