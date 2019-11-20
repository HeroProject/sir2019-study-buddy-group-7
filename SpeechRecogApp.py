import AbstractApplication as Base
from threading import Semaphore

class SpeechRecogApp(Base.AbstractApplication):
    # setup our Application
    def __init__(self):
        super().__init__()

        # Semaphores for async execution. They make sure that the action is completed.
        self.languageLock = Semaphore(0)
        self.textLock = Semaphore(0)
        self.intentLock = Semaphore(0)

        # Attributes of our application
        # Beware that if naming is changed here, the corresponding parameter in DialogeFlow has to be
        # changed as well if it exists
        self.userName = None
        self.intendUnderstood = False

        # Pass the required Dialogflow parameters (add your Dialogflow parameters)
        self.setDialogflowKey('sample_diagFl_key.json')
        self.setDialogflowAgent('sir2019_g7_sample-wfkciw')  # Maybe this must be changed to 'sir2019-g7-sample-wfkciw' which is the project ID

    def main(self):
        print('Main called...')
        # Setting language
        self.setLanguage('en-US')
        print('set language ran.')
        self.languageLock.acquire()
        self.say('Lock acquired. Running...')
        self.textLock.acquire()
        print('Lock acquired. Running...')
        try:
            self.ask('What\'s your name?', 'answer_name')
        except InteractionException:
            self.sayAnimated('Sorry, it was not possible to understand your name. I will go to standby mode now.')
            self.textLock.acquire()
            self.main()

        self.sayAnimated('Oh hi ' + self.userName)
        self.textLock.acquire()

    def onAudioIntent(self, *args, intentName):
        # Something was understood
        self.intendUnderstood = True

        # Assuming we have a DialogueFlow app for the intent "name"
        if intentName == 'answer_name' and len(args) > 0:
            self.userName = args[0]

        self.intentLock.release()

    def onRobotEvent(self, event):
        # make sure all our started actions are completed:
        if event == 'TextDone':
            self.textLock.release()
        elif event == 'LanguageChanged':
            self.languageLock.release()

        # print what is going on
        print(event)

    def ask(self, question, audioContext, attempts=3, timeout=5):
        # We only want the question to be asked once, right?
        self.sayAnimated(question)
        self.textLock.acquire()

        # new question, new stuff to understand
        self.intendUnderstood = False
        while attempts > 0 or not self.intendUnderstood:
            self.setAudioContext(audioContext)
            self.startListening()
            self.intentLock.acquire(timeout=timeout)
            self.stopListening()

            if not self.intendUnderstood:
                self.sayAnimated('Sorry, I didn\'t catch that. Could you please repeat that?')
            self.textLock.acquire()
            attempts -= 1

        if attempts == 0:
            raise InteractionException


class InteractionException(Exception):
    def __init__(self):
        super().__init__()

if __name__ == '__main__':
    print('Initialising the speech recognition app.')
    sample = SpeechRecogApp()
    try:
        # Run the application
        sample.main()
        sample.stop()
    except KeyboardInterrupt:
        print('Early stopping of thread.')
        try:
            sample.stop()
        except Exception as e:
            raise e

