import AbstractApplication as Base
from threading import Semaphore


class SampleApplication(Base.AbstractApplication):
    # setup our Application
    def __init__(self):
        super().__init__()

        # Semaphores for async execution. They make sure that the action is completed.
        self.gesture_lock = Semaphore(0)
        self.language_lock = Semaphore(0)
        self.text_lock = Semaphore(0)
        self.eyecolor_lock = Semaphore(0)
        self.name_lock = Semaphore(0)

        # Attributes of our application
        self.user_name = None

    def main(self):
        # Setting language
        self.setLanguage('en-US')
        self.language_lock.acquire()

        # Change Eyecolor
        self.setEyeColour('red')
        self.eyecolor_lock.acquire()

        # Saying something with body language
        self.sayAnimated('Hello Group 7.')
        self.text_lock.acquire()

        # Say something without moving
        self.say('Boring hello group 7.')
        self.text_lock.acquire()

        # Do a gesture
        # untitled-2ae403 is the ID of the Project in Choreographe.
        # Did not know this in advance, hence the awful name.
        self.doGesture('untitled-2ae403/behavior_1')
        self.gesture_lock.acquire()

        # TODO: How to set this up properly
        # Pass the required Dialogflow parameters (add your Dialogflow parameters)
        # self.setDialogflowKey('<keyfile>.json')
        # self.setDialogflowAgent('<agentname>')

        # Listen for an answer for at most 5 seconds
        # This snipped assumes a DialogueFlow application listening for a name
        self.setAudioContext('answer_name')
        self.startListening()
        self.name_lock.acquire(timeout=5)
        self.stopListening()

    def onAudioIntent(self, *args, intentName):
        # Assuming we have a DialogueFlow app for the intent "name"
        if intentName == 'answer_name' and len(args) > 0:
            self.user_name = args[0]
            self.name_lock.release()

    def onRobotEvent(self, event):
        # make sure all our started actions are completed:
        if event == 'GestureDone':
            self.gesture_lock.release()
        elif event == 'TextDone':
            self.text_lock.release()
        elif event == 'LanguageChanged':
            self.language_lock.release()

        # print what is going on
        print(event)


# Run the application
sample = SampleApplication()
sample.main()
sample.stop()
