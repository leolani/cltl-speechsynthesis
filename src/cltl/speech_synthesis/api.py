import logging.config
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cltl.combot.infra.config.local import LocalConfigurationContainer

# logging.config.fileConfig('config/logging.config')
logger = logging.getLogger(__name__)
# LocalConfigurationContainer.load_configuration()


@dataclass
class SpeechSynthesisInput:
    """Object for the string input.
    """
    value: str


@dataclass
class SpeechSynthesisOutput:
    """Object for the output.
    """
    value: str


class SpeechSynthesisComponent(object):
    """
    Abstract Speech Synthesis Component

    Parameters
    ----------
    language: str
    save_audio: bool
    play_audio: bool
    audios_dir: Path
    """
    _AUDIO_FILE_BUFFER_SIZE = 1024

    def __init__(self, language: str, play_audio: Optional[bool] = True, save_audio: Optional[bool] = True,
                 audios_dir: Optional[Path] = None) -> None:
        self._log = logger.getChild(self.__class__.__name__)

        self._language = language
        self.play_audio = play_audio
        self.save_audio = save_audio

        if audios_dir:
            self.audios_dir = Path(audios_dir)
            self.audios_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.package_home = Path(__file__).parents[3]
            self.audios_dir = self.package_home / "audios"

        logger.info(f'Saving audios to path: {self.audios_dir}')

    def text_to_speech(self, text: SpeechSynthesisInput, audio_file_prefix: str = '') -> SpeechSynthesisOutput:
        """
        Say something through Text to Speech (Implementation)

        Text To Speech Backends should implement this function
        This function should block while speech is being produced

        Parameters
        ----------
        text: SpeechSynthesisInput
        audio_file_prefix: str

        Returns
        -------
        SpeechSynthesisOutput
        """
        raise NotImplementedError()
