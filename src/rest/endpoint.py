from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec.yaml_utils import load_yaml_from_docstring
from marshmallow_dataclass import class_schema

from cltl.speech_synthesis.api import SpeechSynthesisOutput, SpeechSynthesisInput
from cltl.speech_synthesis.mozilla_tts import MozillaTextToSpeech
from cltl.speech_synthesis.wavenet_api import WavenetAPITextToSpeech


class OpenAPISpec:
    def __init__(self, *args, **kwargs):
        self.spec = APISpec(*args, **kwargs)

    @property
    def to_yaml(self):
        return self.spec.to_yaml()

    @property
    def to_dict(self):
        return self.spec.to_dict()

    @property
    def components(self):
        return self.spec.components

    def path(self, path):
        def wrapped(func):
            self.spec.path(path,
                           description=func.__doc__.partition('\n')[0],
                           operations=load_yaml_from_docstring(func.__doc__))
            return func

        return wrapped


api = OpenAPISpec(title="Speech Synthesis Component",
                  version="0.0.1",
                  openapi_version="3.0.2",
                  info=dict(description="Leolani speech synthesis component"),
                  plugins=[MarshmallowPlugin()], )

api.components.schema("SpeechSynthesisInput", schema=class_schema(SpeechSynthesisInput))
api.components.schema("SpeechSynthesisOutput", schema=class_schema(SpeechSynthesisOutput))


@api.path("/speech_synthesis/api/text_to_speech/wavenet")
def text_to_speech_wavenet(input):
    """A text tp speech service using Wavenet voices

    A speech synthesis service to produce speech from text using Google API Text-To_Speech service

    The yaml snippet below is included in the OpenAPI spec for the endpoint:
    ---
    get:
      operationId: rest.endpoint.text_to_speech
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SpeechSynthesisOutput'
          description: Produce speech from a given text
      parameters:
      - in: query
        name: times
        schema:
          $ref: '#/components/schemas/SpeechSynthesisInput'
    """
    return WavenetAPITextToSpeech(language="en-GB").text_to_speech(input)


@api.path("/speech_synthesis/api/text_to_speech/mozilla")
def text_to_speech_mozilla(input):
    """A text tp speech service using Mozilla TTS voices

    A speech synthesis service to produce speech from text using Mozilla TTS service

    The yaml snippet below is included in the OpenAPI spec for the endpoint:
    ---
    get:
      operationId: rest.endpoint.text_to_speech
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SpeechSynthesisOutput'
          description: Produce speech from a given text
      parameters:
      - in: query
        name: times
        schema:
          $ref: '#/components/schemas/SpeechSynthesisInput'
    """
    return MozillaTextToSpeech(language="en-GB").text_to_speech(input)


if __name__ == '__main__':
    with open("speech_synthesis_spec.yaml", "w") as f:
        f.write(api.to_yaml())
