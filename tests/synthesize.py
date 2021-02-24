from leolani.speech_synthesis.system import WavenetAPITextToSpeech, WaveRNNTextToSpeech, MozillaTextToSpeech

application_language = "en-GB"
text = 'Hi my name is Leolani'

# # Wavenet API
wvn_api_tts = WavenetAPITextToSpeech(application_language)
wvn_api_tts.on_text_to_speech(text.format('API'))

# # WaveRNN
# wrnn = WaveRNNTextToSpeech(application_language)
# wrnn.on_text_to_speech(text.format('WaveRNN'))

# Mozilla TTS
moz = MozillaTextToSpeech(application_language)
moz.on_text_to_speech(text.format('Mozilla TTS'))
