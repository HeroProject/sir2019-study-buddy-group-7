import time
from pathlib import Path
from threading import Thread

import redis


class AbstractApplication(object):
    __topics = ["events_robot", "detected_person", "recognised_face", "audio_language", "audio_intent", "audio_newfile",
                "text_speech", "picture_newfile"]

    def __init__(self):
        self.__redis = redis.Redis()
        self.__pubsub = self.__redis.pubsub(ignore_subscribe_messages=True)
        self.__pubsub.subscribe(*self.__topics)
        t = Thread(target=self.__listen)
        t.start()

    def __listen(self):
        self.__running = True
        while self.__running:
            message = self.__pubsub.get_message()
            if message is not None:
                channel = message['channel'].decode()
                data = message['data'].decode()
                #print("received " + data + " on " + channel)
                if channel == self.__topics[0]:
                    self.onRobotEvent(event=data)
                elif channel == self.__topics[1]:
                    self.onPersonDetected()
                elif channel == self.__topics[2]:
                    self.onFaceRecognized(identifier=data)
                elif channel == self.__topics[3]:
                    self.onAudioLanguage(languageKey=data)
                elif channel == self.__topics[4]:
                    data = data.split("|")
                    self.onAudioIntent(intentName=data[0], *data[1:])
                elif channel == self.__topics[5]:
                    self.onNewAudioFile(audioFile=data)
                elif channel == self.__topics[6]:
                    self.onSpeechText(text=data)
                elif channel == self.__topics[7]:
                    self.onNewPictureFile(pictureFile=data)
            else:
                time.sleep(0.001)
        self.__pubsub.close()

    def __send(self, channel, data):
        self.__redis.publish(channel, data)
        #print("sent " + data + " on " + channel)

    def stop(self):
        """Stop listening to incoming events (which is done in a thread) so the Python application can close."""
        self.__running = False

    def onRobotEvent(self, event):
        """Triggered upon an event from the robot. This can be either an event related to some action called here,
        i.e. one of: GestureStarted, GestureDone, PlayAudioStarted, PlayAudioDone, TextStarted, TextDone,
        EyeColourStarted, EyeColourDone, SetIdle, SetNonIdle or LanguageChanged;
        or an event related to one of the robot's touch sensors, i.e. one of:
        RightBumperPressed, LeftBumperPressed, BackBumperPressed, FrontTactilTouched, MiddleTactilTouched,
        RearTactilTouched, HandRightBackTouched, HandRightLeftTouched, HandRightRightTouched, HandLeftLeftTouched,
        HandLeftRightTouched or HandLeftBackTouched (http://doc.aldebaran.com/2-5/family/robots/contact-sensors_robot.html)."""
        pass

    def onPersonDetected(self):
        """Triggered when some person was detected in front of the robot (after a startWatching action was called).
        Only sent when the people detection service is running. Will be sent as long as a person is detected."""
        pass

    def onFaceRecognized(self, identifier):
        """Triggered when a specific face was detected in front of the robot (after a startWatching action was called).
        Only sent when the face recognition service is running. Will be sent as long as the face is recognised.
        The identifiers of recognised faces are stored in a file, and will thus persist over a restart of the agent."""
        pass

    def onAudioLanguage(self, languageKey):
        """Triggered whenever a language change was requested (for example by the user).
        Given is the full language key (e.g. nl-NL or en-US)."""
        pass

    def onAudioIntent(self, *args, intentName):
        """Triggered whenever an intent was detected (by Dialogflow) on a user's speech.
        Given is the name of intent and a list of optional parameters (following from the dialogflow spec).
        See https://cloud.google.com/dialogflow/docs/intents-actions-parameters.
        These be sent as soon as an intent is recognised, which is always after some startListening action,
        but might come in some time after the final stopListening action (if there was some intent detected at least).
        Intents will keep being recognised until stopListening is called."""
        pass

    def onNewAudioFile(self, audioFile):
        """Triggered whenever a new recording has been stored to an audio (WAV) file. See setRecordAudio.
        Given is the name to the recorded file (which is in the folder required by the playAudio function).
        All audio received between the last startListening and stopListening calls is recorded."""
        pass

    def onSpeechText(self, text):
        """Triggered whenever text has been recognized (by Dialogflow) from a user's speech.
        Given is the recognized text(string). Also sent if no intent was recognised from the text."""
        pass

    def onNewPictureFile(self, pictureFile):
        """Triggered whenever a new picture has been stored to an image (JPG) file. See takePicture.
        Given is the path to the taken picture."""
        pass

    ##
    # Above are the on### 'event functions'; below are the 'action functions' only.
    ##

    def setDialogflowKey(self, keyFile):
        """Required for setting up Dialogflow: the path to the (JSON) keyfile."""
        contents = Path(keyFile).read_text()
        self.__send('dialogflow_key', contents)

    def setDialogflowAgent(self, agentName):
        """Required for setting up Dialogflow: the name of the agent to use."""
        self.__send('dialogflow_agent', agentName)

    def setLanguage(self, languageKey):
        """Required for setting up Dialogflow (and the robot itself): the full key of the language to use
        (e.g. nl-NL or en-US). A LanguageChanged event will be sent when the change has propagated."""
        self.__send('audio_language', languageKey)

    def setRecordAudio(self, shouldRecord):
        """Indicate if audio should be recorded (see onNewAudioFile)."""
        self.__send('dialogflow_record', '1' if shouldRecord else '0')

    def setAudioContext(self, context):
        """Indicate the Dialogflow context to use for the next speech-to-text (or to intent)."""
        self.__send('audio_context', context)

    def setAudioHints(self, *args):
        """Pass hints to Dialogflow about the words that it should recognize especially."""
        self.__send('audio_hints', '|'.join(args))

    def startListening(self):
        """Tell the robot (and Dialogflow) to start listening to audio (and potentially recording it).
        Intents will be continuously recognised. At some point stopListening needs to be called!"""
        self.__send('action_audio', 'start listening')

    def stopListening(self):
        """Tell the robot (and Dialogflow) to stop listening to audio.
        Note that a potentially recognized intent might come in up to a second after this call."""
        self.__send('action_audio', 'stop listening')

    def setIdle(self):
        """Put the robot into 'idle mode': always looking straight ahead.
        A SetIdle event will be sent when the robot has transitioned into the idle mode."""
        self.__send('action_idle', 'true')

    def setNonIdle(self):
        """Put the robot back into its default 'autonomous mode' (looking towards sounds).
        A SetNonIdle event will be sent when the robot has transitioned out of the idle mode."""
        self.__send('action_idle', 'false')

    def startLooking(self):
        """Tell the robot (and any recognition module) to start the camera feed).
        At some point stopLooking need sto be called!"""
        self.__send('action_video', 'start watching')

    def stopLooking(self):
        """Tell the robot (and Dialogflow) to stop listening to audio.
        Note that a potentially recognized intent might come in a bit later than this call."""
        self.__send('action_video', 'stop watching')

    def say(self, text):
        """A string that the robot should say (in the currently selected language!).
        A TextStarted event will be sent when the speaking starts and a TextDone event after it is finished."""
        self.__send('action_say', text)

    def sayAnimated(self, text):
        """A string that the robot should say (in the currently selected language!) in an animated fashion.
        This means that the robot will automatically try to add (small) animations to the text.
        Moreover, in this function, special tags are supported, please see:
        http://doc.aldebaran.com/2-5/naoqi/audio/altexttospeech-tuto.html#using-tags-for-voice-tuning
        A TextStarted event will be sent when the speaking starts and a TextDone event after it is finished."""
        self.__send('action_say_animated', text)

    def doGesture(self, gesture):
        """Make the robot perform the given gesture. The list of available gestures is available on:
        http://doc.aldebaran.com/2-5/naoqi/motion/alanimationplayer-advanced.html
        A GestureStarted event will be sent when the gesture starts and a GestureDone event when it is finished."""
        self.__send('action_gesture', gesture)

    def playAudio(self, audioFile):
        """Plays the audio file (in the tablet's html/audio directory) on the robot's speakers.
        A PlayAudioStarted event will be sent when the audio starts and a PlayAudioDone event after it is finished.
        Any previously playing audio will be cancelled first;
        calling playAudio with an empty string thus has the effect of cancelling any previously playing audio."""
        self.__send('action_play_audio', audioFile)

    def setEyeColour(self, colour):
        """Sets the robot's eye LEDs to one of the following colours:
        white, red, green, blue, yellow, magenta, cyan, greenyellow or rainbow.
        An EyeColourStarted event will be sent when the change starts and a EyeColourDone event after it is done."""
        self.__send('action_eyecolour', colour)

    def takePicture(self):
        """Instructs the robot to take a picture. See the onNewPictureFile function."""
        self.__send('action_take_picture', '')

    def turnLeft(self):
        """Instructs the (Pepper) robot to make a left-hand turn."""
        self.__send('action_turn', 'left')

    def turnRight(self):
        """Instructs the (Pepper) robot to make a right-hand turn."""
        self.__send('action_turn', 'right')
