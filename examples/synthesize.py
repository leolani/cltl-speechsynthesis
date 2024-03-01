from cltl.speech_synthesis.mozilla_tts import MozillaTextToSpeech
#from cltl.speech_synthesis.wavenet_api import WavenetAPITextToSpeech
from gtts import gTTS

application_language = "en-GB"
application_language = "nl"

text = 'Hoi ik ben Leo Lani'

# # Wavenet API
#wvn_api_tts = WavenetAPITextToSpeech(application_language, save_audio=False)
#wvn_api_tts.text_to_speech(text)
#
# # Mozilla TTS
#moz = MozillaTextToSpeech(application_language, save_audio=False)
#moz.text_to_speech(text)


from gtts import gTTS
from playsound import playsound
text = 'Hallo Thomas. Hoe gaat het met je?'
language = 'nl'
myobj = gTTS(text=text, lang=language, slow=False)
myobj.save("mytext2speech.mp3")
playsound("./mytext2speech.mp3")
