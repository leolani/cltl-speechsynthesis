from cltl.speech_synthesis.mozilla_tts import MozillaTextToSpeech
from cltl.speech_synthesis.wavenet_api import WavenetAPITextToSpeech

application_language = "en-GB"
text = 'Hi'

# # Wavenet API
wvn_api_tts = WavenetAPITextToSpeech(application_language, save_audio=False)
wvn_api_tts.text_to_speech(text)
#
# # Mozilla TTS
moz = MozillaTextToSpeech(application_language, save_audio=False)
moz.text_to_speech(text)
