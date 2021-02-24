# cltl-tts
A text to speech service.
This service expects a text and outputs an audio file.
In the end, the voice should also be configurable.


## Installation
Python >= 3.7

```bash
conda create --name cltl-tts python=3.7
pip install -r requirements.txt
```

### Submodules
This project depends on several independent Speech Synthesis repositories (e.g. WaveRNN). Initialize the submodules like this:

```bash
git submodule init
```

Set up Pycharm to use the submodule if needed, as explained [here](https://stackoverflow.com/a/54234581)

## TTS implementations

### WaveRNN
To use WaveRNN please extract the contents of the zip files in the ```pretrained``` folder to have the following structure:
```
WaveRNN
    pretrained
        tts_weights --> extracted contents from ljspeech.tacotron.r2.180k.zip
            latest_weights.pyt
        voc_weights --> extracted contents from ljspeech.wavernn.mol.800k.zip
            latest_weights.pyt
        ljspeech.wavernn.mol.800k.zip
        tacotron.r2.180k 
```

Alternatively you can run the following small python script

```python
import os
import zipfile

os.makedirs('/ABSOLUTE/PATH/TO/REPOSITORY/cltl-tts/leolani/speech_synthesis/WaveRNN/pretrained/voc_weights/', exist_ok=True)
zip_ref = zipfile.ZipFile('/ABSOLUTE/PATH/TO/REPOSITORY/cltl-tts/leolani/speech_synthesis/WaveRNN/pretrained/ljspeech.wavernn.mol.800k.zip', 'r')
zip_ref.extractall('/ABSOLUTE/PATH/TO/REPOSITORY/cltl-tts/leolani/speech_synthesis/WaveRNN/pretrained/voc_weights/')
zip_ref.close()

os.makedirs('/ABSOLUTE/PATH/TO/REPOSITORY/cltl-tts/leolani/speech_synthesis/WaveRNN/pretrained/tts_weights/', exist_ok=True)
zip_ref = zipfile.ZipFile('/ABSOLUTE/PATH/TO/REPOSITORY/cltl-tts/leolani/speech_synthesis/WaveRNN/pretrained/ljspeech.tacotron.r2.180k.zip', 'r')
zip_ref.extractall('/ABSOLUTE/PATH/TO/REPOSITORY/cltl-tts/leolani/speech_synthesis/WaveRNN/pretrained/tts_weights/')
zip_ref.close()
```

### Mozilla TTS

To use the Mozilla TTS services please get the docker image running beforehand, for example like this:
``` bash
docker run -it -p 5002:5002 synesthesiam/mozillatts:en
```


### Description

This package contains multiple implementations to create spoken language for any written text. The modules planned are:

- [X] WaveNet by Google (calling API)
- [ ] WaveNet (Local implementation) - Started with [r9y9's mplementation](https://github.com/r9y9/wavenet_vocoder) but ran into several problems with package versioning
- [X] WaveRNN (Bug: cannot play audio back with wave) - [implementation by fatchord](https://github.com/fatchord/WaveRNN)
- [ ] Glow-TTS - [this implementation](https://github.com/jaywalnut310/glow-tts)
- [X] Mozilla-TTS - [docker by synesthesiam](https://github.com/synesthesiam/docker-mozillatts)