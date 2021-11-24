# cltl-speechsynthesis

A Speech synthesis (text to speech) service. This service expects a text and outputs an audio file. Different voices are
implemented.

### Description

This package contains multiple implementations to create spoken language for any written text. The different voices implementeda are:

- [X] WaveNet
- [X] Mozilla-TTS

## Installation

This repository uses Python >= 3.7. To set ip up you can run

```bash
conda create --name cltl-speechsynthesis python=3.7
conda activate cltl-speechsynthesis
pip install -e .
```

## Speech Synthesis implementations

### Wavenet voices provided by Google API

To use this voices you need to create a project on
the [Google Cloud Platform](https://cloud.google.com/speech-to-text/docs/quickstart-client-libraries) supporting
Text-To-Speech APIs.

Put the `google_cloud_key.json` file in the `config` folder of this repo. 

### Mozilla TTS

To use the Mozilla TTS services please get
the [docker image by synesthesiam](https://github.com/synesthesiam/docker-mozillatts) running beforehand, for example
like this:

``` bash
docker run -it -p 5002:5002 synesthesiam/mozillatts:en
```

## To DO

- Fix logging
- Fix config of language, save/play audio file, audio directory
- Event infrastructure
- App
- Check if we can switch voices via different APIs
- Check implementation middle layer