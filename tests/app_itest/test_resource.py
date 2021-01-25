import logging
import sys
import threading
import unittest
from time import sleep

import importlib_resources
import mock
import numpy as np

from pepper.framework.application.intention import AbstractIntention
from pepper.framework.backend.abstract.microphone import AbstractMicrophone
from leolani.speech_synthesis.abstract.text_to_speech import AbstractTextToSpeech
from pepper.framework.application.application import AbstractApplication
from pepper.framework.backend.abstract.backend import AbstractBackend
from pepper.framework.backend.container import BackendContainer
from pepper.framework.application.speech_recognition import SpeechRecognitionComponent
from pepper.framework.application.text_to_speech import TextToSpeechComponent
from pepper.framework.infra.config.api import ConfigurationContainer
from pepper.framework.infra.config.local import LocalConfigurationContainer
from pepper.framework.infra.di_container import singleton, DIContainer
from pepper.framework.infra.event.api import EventBusContainer
from pepper.framework.infra.event.memory import SynchronousEventBusContainer
from pepper.framework.infra.resource.api import ResourceContainer
from pepper.framework.infra.resource.threaded import ThreadedResourceContainer
from pepper.framework.sensor.api import AbstractTranslator, AbstractASR, UtteranceHypothesis, SensorContainer
from pepper.framework.sensor.container import DefaultSensorWorkerContainer
from pepper.framework.sensor.vad import AbstractVAD
from test import util


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
logger.setLevel(logging.ERROR)


AUDIO_FRAME = np.zeros(80).astype(np.int16)


def setupTestComponents():
    """Workaround to overwrite static state in DIContainers across tests"""
    global TestIntention
    global TestApplication

    with importlib_resources.path(__package__, "test.config") as test_config:
        LocalConfigurationContainer.load_configuration(str(test_config), [])

    class TestBackendContainer(BackendContainer, EventBusContainer, ResourceContainer):
        @property
        @singleton
        def backend(self):
            return TestBackend(self.event_bus, self.resource_manager)

    class TestTextToSpeech(AbstractTextToSpeech):
        def __init__(self, event_bus, resource_manager):
            super(TestTextToSpeech, self).__init__("nl", event_bus, resource_manager)
            self.latch = threading.Event()
            self.utterances = []

        def on_text_to_speech(self, text, animation=None):
            # type: (Union[str, unicode], Optional[str]) -> None
            self.latch.wait()
            self.utterances.append(text)


    class TestBackend(AbstractBackend):
        def __init__(self, event_bus, resource_manager):
            super(TestBackend, self).__init__(microphone=AbstractMicrophone(8000, 1, event_bus, resource_manager),
                                              text_to_speech=TestTextToSpeech(event_bus, resource_manager),
                                              camera=None, motion=None, led=None, tablet=None)


    class TestVAD(AbstractVAD):
        def __init__(self, resource_manager, configuration_manager):
            super(TestVAD, self).__init__(resource_manager, configuration_manager)
            self.speech_flag = ThreadsafeBoolean()

        def _is_speech(self, frame):
            return self.speech_flag.val


    class TestSensorContainer(BackendContainer, SensorContainer, ConfigurationContainer):
        @property
        @singleton
        def vad(self):
            return TestVAD(self.resource_manager, self.config_manager)

        def asr(self, language="nl"):
            mock_asr = mock.create_autospec(AbstractASR)
            mock_asr.transcribe.return_value = [UtteranceHypothesis("Test one two", 1.0)]

            return mock_asr

        def translator(self, source_language, target_language):
            mock_translator = mock.create_autospec(AbstractTranslator)
            mock_translator.translate.side_effect = lambda text: "Translated: " + text

            return mock_translator

        @property
        def face_detector(self):
            return None

        def object_detector(self, target):
            return None


    class ApplicationContainer(TestBackendContainer,
                               TestSensorContainer,
                               SynchronousEventBusContainer,
                               ThreadedResourceContainer,
                               LocalConfigurationContainer):
        pass


    class TestIntention(ApplicationContainer, AbstractIntention, DefaultSensorWorkerContainer,
                          SpeechRecognitionComponent, TextToSpeechComponent):
        def __init__(self):
            super(TestIntention, self).__init__()
            self.hypotheses = []

        def on_transcript(self, hypotheses, audio):
            self.hypotheses.extend(hypotheses)


    class TestApplication(AbstractApplication, ApplicationContainer):
        def __init__(self, intention):
            super(TestApplication, self).__init__(intention)


class ListeningThread(threading.Thread):
    def __init__(self, speech_flag, microphone, webrtc_buffer_size, name="Listening"):
        super(ListeningThread, self).__init__(name=name)
        self._webrtc_buffer_size = webrtc_buffer_size
        self._speech_flag = speech_flag
        self._microphone = microphone
        self.running = True
        self.listen_to_frames = False
        self.listening_latch = threading.Event()
        self.exit_latch = threading.Event()
        self.continue_speech_latch = threading.Event()
        self.in_speech_latch = threading.Event()

    def stop(self):
        self.running = False
        self.exit_latch.wait(1)
        self.listening_latch.set()
        self.exit_latch.set()
        self.continue_speech_latch.set()
        self.in_speech_latch.set()

    def listen(self, frames, continue_latch=False):
        self.in_speech_latch = threading.Event()
        self.continue_speech_latch = threading.Event()
        self.exit_latch = threading.Event()
        self.listen_to_frames = frames
        self.listening_latch.set()

        if continue_latch:
            return self.in_speech_latch, self.exit_latch, self.continue_speech_latch
        else:
            self.continue_speech_latch.set()
            return self.in_speech_latch, self.exit_latch

    def run(self):
        logger.debug("Thread %s started", self.name)
        self.listening_latch.wait()
        while self.running:
            logger.debug("Started listening")
            for i in range(self.listen_to_frames):
                self._speech_flag.val = True
                # Fill speech buffer
                buffer_size = self._webrtc_buffer_size
                for j in range(2 * buffer_size + 10):
                    self._microphone.on_audio(AUDIO_FRAME)
                    logger.debug("Listened to frame %s-%s", i, j)
                    sleep(0.001)

                self.in_speech_latch.set()
                self.continue_speech_latch.wait()

                self._speech_flag.val = False
                # Empty speech buffer
                for j in range(buffer_size + 10):
                    self._microphone.on_audio(AUDIO_FRAME)
                    logger.debug("Void %s-%s", i, j)
                    sleep(0.001)

            self.listening_latch.clear()
            logger.debug("Stopped listening")
            self.exit_latch.set()
            self.listening_latch.wait()

        logger.debug("Thread %s stopped", self.name)

class TalkingThread(threading.Thread):
    def __init__(self, intention, name="Talking"):
        super(TalkingThread, self).__init__(name=name)
        self._intention = intention
        self.running = True
        self.talking = False
        self.talking_latch = threading.Event()
        self.exit_latch = threading.Event()

    def stop(self):
        self.running = False
        self.exit_latch.wait(1)
        self.talking_latch.set()
        self.exit_latch.set()

    def talk(self, utterances):
        self.exit_latch = threading.Event()
        self.utterances = utterances
        self.talking_latch.set()

        return self.exit_latch

    def run(self):
        logger.debug("Thread % started", self.name)
        self.talking_latch.wait()
        while self.running:
            logger.debug("Started talking")
            for utterance in self.utterances:
                self._intention.say(utterance, block=True)
                logger.debug("Said utterance")
                sleep(0.001)

            self.talking_latch.clear()
            logger.debug("Stopped talking")
            self.exit_latch.set()
            self.talking_latch.wait()

        logger.debug("Thread %s stopped", self.name)


class ResourceITest(unittest.TestCase):
    def setUp(self):
        setupTestComponents()
        self.intention = TestIntention()
        self.application = TestApplication(self.intention)
        self.application._start()

        sleep(1)

        webrtc_buffer_size = self.intention.config_manager\
            .get_config("pepper.framework.sensors.vad.webrtc")\
            .get_int("buffer_size")
        self.threads = [ListeningThread(self.intention.vad.speech_flag, self.intention.backend.microphone, webrtc_buffer_size),
                        TalkingThread(self.intention)]
        for thread in self.threads:
            thread.start()

    def tearDown(self):
        self.application._stop()

        for thread in self.threads:
            thread.stop()
            thread.join()

        del self.application
        DIContainer._singletons.clear()

        # Try to ensure that the application is stopped
        try:
            util.await_predicate(lambda: threading.active_count() < 2, max=100)
        except:
            sleep(1)

    def test_listen(self):
        listening_thread, _ = self.threads

        _, exit_speech_latch = listening_thread.listen(2)
        exit_speech_latch.wait()

        sleep(0.1)

        self.assertEqual(2, len(self.intention.hypotheses))
        self.assertEqual('Test one two', self.intention.hypotheses[0].transcript)
        self.assertEqual(1.0, self.intention.hypotheses[0].confidence)
        self.assertEqual('Test one two', self.intention.hypotheses[1].transcript)
        self.assertEqual(1.0, self.intention.hypotheses[1].confidence)

    def test_talk(self):
        self.intention.backend.text_to_speech.latch.set()

        _, talking_thread = self.threads

        talk_latch = talking_thread.talk(["Test"])

        self.assertTrue(talk_latch.wait())

        sleep(0.1)

        self.assertEqual(1, len(self.intention.backend.text_to_speech.utterances))
        self.assertEqual("Test", self.intention.backend.text_to_speech.utterances[0])

    def test_talk_after_vad_stops(self):
        self.intention.backend.text_to_speech.latch.set()
        listening_thread, talking_thread = self.threads

        in_speech_latch, exit_speech_latch, continue_speech_latch = listening_thread.listen(1, continue_latch=True)
        in_speech_latch.wait()

        exit_talk_latch = talking_thread.talk(["Test"])
        self.assertFalse(exit_talk_latch.wait(0.5))

        continue_speech_latch.set()
        exit_speech_latch.wait()

        exit_talk_latch.wait()

        sleep(0.1)

        self.assertEqual(1, len(self.intention.backend.text_to_speech.utterances))
        self.assertEqual("Test", self.intention.backend.text_to_speech.utterances[0])

    def test_listen_after_talk_stops(self):
        listening_thread, talking_thread = self.threads

        in_speech_latch, exit_speech_latch, continue_speech_latch = listening_thread.listen(1, continue_latch=True)
        in_speech_latch.wait()

        exit_talk_latch = talking_thread.talk(["Test"])
        self.assertFalse(exit_talk_latch.wait(0.5))

        continue_speech_latch.set()
        exit_speech_latch.wait()

        # Ignoring speech while talking
        self.assertEqual(1, len(self.intention.hypotheses))
        self.assertEqual('Test one two', self.intention.hypotheses[0].transcript)
        self.assertEqual(1.0, self.intention.hypotheses[0].confidence)

        _, exit_speech_latch = listening_thread.listen(1)
        exit_speech_latch.wait()

        self.assertEqual(1, len(self.intention.hypotheses))
        self.assertEqual('Test one two', self.intention.hypotheses[0].transcript)
        self.assertEqual(1.0, self.intention.hypotheses[0].confidence)

        # Pick up speech again after talking
        _, exit_speech_latch, continue_speech_latch = listening_thread.listen(1, continue_latch=True)

        continue_speech_latch.set()
        self.intention.backend.text_to_speech.latch.set()
        exit_talk_latch.wait()
        exit_speech_latch.wait()

        sleep(0.1)

        self.assertEqual(2, len(self.intention.hypotheses))
        self.assertEqual('Test one two', self.intention.hypotheses[0].transcript)
        self.assertEqual(1.0, self.intention.hypotheses[0].confidence)
        self.assertEqual('Test one two', self.intention.hypotheses[1].transcript)
        self.assertEqual(1.0, self.intention.hypotheses[1].confidence)

    def await_predicate(self, predicate, max=100, msg="predicate"):
        cnt = 0
        while not predicate() and cnt < max:
            sleep(0.01)
            cnt += 1

        if cnt == max:
            self.fail("Test timed out waiting for " + msg)


class ThreadsafeBoolean(object):
    def __init__(self):
        self._value = False
        self._lock = threading.Lock()

    @property
    def val(self):
        with self._lock:
            return self._value

    @val.setter
    def val(self, value):
        with self._lock:
            self._value = value

if __name__ == '__main__':
    unittest.main()