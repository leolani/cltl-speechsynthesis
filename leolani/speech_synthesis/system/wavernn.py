import zipfile

import datetime
import os
import torch

from leolani.speech_synthesis.WaveRNN.models.fatchord_version import WaveRNN
from leolani.speech_synthesis.WaveRNN.models.tacotron import Tacotron
from leolani.speech_synthesis.WaveRNN.utils import hparams as hp
from leolani.speech_synthesis.WaveRNN.utils.display import simple_table
from leolani.speech_synthesis.WaveRNN.utils.text import symbols
from leolani.speech_synthesis.WaveRNN.utils.text import text_to_sequence
from leolani.speech_synthesis.abstract.text_to_speech import AbstractTextToSpeech

os.makedirs('quick_start/tts_weights/', exist_ok=True)
os.makedirs('quick_start/voc_weights/', exist_ok=True)

zip_ref = zipfile.ZipFile('pretrained/ljspeech.wavernn.mol.800k.zip', 'r')
zip_ref.extractall('quick_start/voc_weights/')
zip_ref.close()

zip_ref = zipfile.ZipFile('pretrained/ljspeech.tacotron.r2.180k.zip', 'r')
zip_ref.extractall('quick_start/tts_weights/')
zip_ref.close()


class WaveRNNTextToSpeech(AbstractTextToSpeech):
    """
    System Text to Speech

    Parameters
    ----------
    language: str
        `Language Code `_
    """

    def __init__(self, language, batched=True, force_cpu=True):
        # type: (str) -> None
        AbstractTextToSpeech.__init__(self, language)
        hp.configure('hparams.py')  # Load hparams from file

        self.batched = batched

        # Select device to use
        self.device = self._select_device(force_cpu)

        # Initialize waveRNN
        self.voc_model = self._initialize_wavernn()

        # Initialize tacotron
        self.tts_model = self._initialize_tacotron()

        self._log.debug("Booted (text -> speech)")

    def _select_device(self, force_cpu):
        if not force_cpu and torch.cuda.is_available():
            device = torch.device('cuda')
        else:
            device = torch.device('cpu')
        self._log.debug('Using device:', self.device)

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

        voc_model.load('quick_start/voc_weights/latest_weights.pyt')

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

        tts_model.load('quick_start/tts_weights/latest_weights.pyt')

        return tts_model

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
                input_text = text
                inputs = [text_to_sequence(input_text.strip(), hp.tts_cleaner_names)]

                voc_k = self.voc_model.get_step() // 1000
                tts_k = self.tts_model.get_step() // 1000

                r = self.tts_model.r

                simple_table([('WaveRNN', str(voc_k) + 'k'),
                              (f'Tacotron(r={r})', str(tts_k) + 'k'),
                              ('Generation Mode', 'Batched' if self.batched else 'Unbatched'),
                              ('Target Samples', 11_000 if self.batched else 'N/A'),
                              ('Overlap Samples', 550 if self.batched else 'N/A')])

                for inp, x in enumerate(inputs, 1):
                    self._log.debug(f'| Generating {inp}/{len(inputs)}')
                    file = self._create_sound(x)

                    if play_file:
                        self._play_file(file)

                    if not save_file:
                        self._delete_file(file)

                return
            except:
                self._log.exception("Couldn't Synthesize Speech ({})".format(i + 1))

    def _create_sound(self, x):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        tmp_file = os.path.join(dir_path, "../../audios/{}.wav".format(datetime.now().strftime('%Y-%m-%d-%H-%M')))

        try:
            _, m, attention = self.tts_model.generate(x)
            m = torch.tensor(m).unsqueeze(0)
            m = (m + 4) / 8

            self.voc_model.generate(m, tmp_file, self.batched, 11_000, 550, hp.mu_law)

            self._log.debug("Audio content written to file '{}'".format(tmp_file))

        except:
            self._log.exception("Failed to write temporary file")

        return tmp_file
