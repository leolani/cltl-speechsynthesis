# cltl-tts
A text to speech service.
This service expects a text and outputs an audio file.
In the end, the voice should also be configurable.





## Installation

Python >= 3.6 

```bash
conda create --name cltl-tts python=3
pip install -r requirements.txt
```

Initialize the submodules

```bash
git submodule init
```


Create a sublink so the import work


### Description

This package contains multiple implementations to create spoken language for any written text. The modules planned are:

- [X] WaveNet by Google (calling API)
- [ ] WaveNet (Local implementation) - Started with [r9y9's mplementation](https://github.com/r9y9/wavenet_vocoder) but ran into several problems with package versioning
- [ ] WaveRNN - In progress
- [ ] Glow-TTS - [this implementation](https://github.com/jaywalnut310/glow-tts)
- [ ] Mozilla-TTS - [docker by](https://github.com/synesthesiam/docker-mozillatts)