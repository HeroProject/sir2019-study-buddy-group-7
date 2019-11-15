import AbstractApplication as Base
from threading import Semaphore


class SampleApplication(Base.AbstractApplication):
    # setup our Application
    def __init__(self):
        super().__init__()

        # Semaphores for async execution. They make sure that the action is completed.
        self.gestureLock = Semaphore(0)
        self.languageLock = Semaphore(0)
        self.textLock = Semaphore(0)
        self.eyeColorLock = Semaphore(0)
        self.nameLock = Semaphore(0)

        # Attributes of our application
        # Beware that if naming is changed here, the corresponding parameter in DialogeFlow has to be
        # changed as well if it exists
        self.userName = None

    def main(self):
        # Setting language
        self.setLanguage('en-US')
        self.languageLock.acquire()

        # Change Eyecolor
        self.setEyeColour('red')
        self.eyeColorLock.acquire()

        # Saying something with body language
        self.sayAnimated('Hello Group 7.')
        self.textLock.acquire()

        # Say something without moving
        self.say('Boring hello group 7.')
        self.textLock.acquire()

        # Do a gesture
        # untitled-2ae403 is the ID of the Project in Choreographe.
        # Did not know this in advance, hence the awful name.
        self.doGesture('untitled-2ae403/behavior_1')
        self.gestureLock.acquire()

        # Pass the required Dialogflow parameters (add your Dialogflow parameters)
        self.setDialogflowKey('sample_diagFl_key.json')
        self.setDialogflowAgent('sir2019_g7_sample') # Maybe this must be changed to 'sir2019-g7-sample-wfkciw' which is the project ID

        # Listen for an answer for at most 5 seconds
        # This snipped assumes a DialogueFlow application listening for a name
        self.setAudioContext('answer_name')
        self.startListening()
        self.nameLock.acquire(timeout=5)
        self.stopListening()

    def onAudioIntent(self, *args, intentName):
        # Assuming we have a DialogueFlow app for the intent "name"
        if intentName == 'answer_name' and len(args) > 0:
            self.userName = args[0]
            self.nameLock.release()

    def onRobotEvent(self, event):
        # make sure all our started actions are completed:
        if event == 'GestureDone':
            self.gestureLock.release()
        elif event == 'TextDone':
            self.textLock.release()
        elif event == 'LanguageChanged':
            self.languageLock.release()
        elif event == 'EyeColourDone':
            self.eyeColorLock.release()

        # print what is going on
        print(event)


# Run the application
sample = SampleApplication()
sample.main()
sample.stop()
