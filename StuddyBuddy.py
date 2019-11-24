import AbstractApplication as Base
from threading import Semaphore
# from loguru import logger


class StudyBuddyApp(Base.AbstractApplication):
    # setup our Application
    def __init__(self):
        super().__init__()

        # Semaphores for async execution. They make sure that the action is completed.
        self.languageLock = Semaphore(0)
        self.textLock = Semaphore(0)
        self.intentLock = Semaphore(0)
        self.gestureLock = Semaphore(0)

        # Attributes of our application
        self.intendUnderstood = False
        self.activation = False
        self.userName = None
        self.studentsFeeling = None
        self.changingWish = None
        self.schedule = None
        self.timeLeft = None
        self.toDo = None

        # Pass the required Dialogflow parameters (add your Dialogflow parameters)
        self.setDialogflowKey('production_diagFl_key.json')
        self.setDialogflowAgent('sir-study-buddy-258913')

    def main(self):
        # Setting language
        self.setLanguage('en-US')
        self.languageLock.acquire()

        self.setAudioContext('activation')
        # wait for activation
        self.startListening()
        while not self.activation:
            self.intentLock.acquire(timeout=5)
        self.stopListening()

    def onAudioIntent(self, *args, intentName):
        self.intendUnderstood = True
        if intentName == 'activation':
            self.activation = True
        elif intentName == 'answer_name':
            if len(args) > 0:
                self.userName = args[0]
        elif intentName == 'students_feeling':
            pass
        elif intentName == 'changing_wish':
            pass
        elif intentName == 'schedule':
            pass
        elif intentName == 'time_left':
            pass
        elif intentName == 'to_do':
            pass

    def onRobotEvent(self, event):
        # make sure all our started actions are completed:
        if event == 'TextDone':
            self.textLock.release()
        elif event == 'LanguageChanged':
            self.languageLock.release()

    def ask(self, question, audioContext, attempts=3, timeout=5):
        # We only want the question to be asked once, right?
        self.sayAnimated(question)
        self.textLock.acquire()

        # new question, new stuff to understand
        self.intendUnderstood = False
        while attempts > 0 and not self.intendUnderstood:
            attempts -= 1
            self.setAudioContext(audioContext)
            self.startListening()
            self.intentLock.acquire(timeout=timeout)
            self.stopListening()
            if not self.intendUnderstood and attempts > 0:
                self.sayAnimated('Sorry, I didn\'t catch that. Could you please repeat that?')
                self.textLock.acquire()
        if attempts == 0:
            raise InteractionException


class InteractionException(Exception):
    def __init__(self):
        super().__init__()


if __name__ == '__main__':
    sample = StudyBuddyApp()
    try:
        # Run the application
        sample.main()
        sample.stop()
    except KeyboardInterrupt:
        try:
            sample.stop()
        except Exception as e:
            raise e