from cltl.speech_synthesis.wavenet_api import WavenetAPITextToSpeech
from cltl.speech_synthesis.mozilla_tts import MozillaTextToSpeech

application_language = "en-GB"
text = 'Hi'

# # Wavenet API
wvn_api_tts = WavenetAPITextToSpeech(application_language, save_audio=False)
wvn_api_tts.text_to_speech(text.format('API'))
#
# # Mozilla TTS
moz = MozillaTextToSpeech(application_language, save_audio=False)
moz.text_to_speech(text.format('Mozilla TTS'))

# other tests
# empty input, empty output (file exists), proper audio created (difficult but it might)
# test when it breaks
# tests are easier if rest is implemented
# testing eventbus is also doable, but not needed now

# integration? tests (kinda)
# this should test that my API and the rest/eventbus are the same. should be trivial and not-worthy atm
