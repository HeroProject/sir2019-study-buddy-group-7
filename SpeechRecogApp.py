import AbstractApplication as Base
from threading import Semaphore
from loguru import logger


class SpeechRecogApp(Base.AbstractApplication):
    # setup our Application
    def __init__(self):
        super().__init__()

        # Semaphores for async execution. They make sure that the action is completed.
        self.languageLock = Semaphore(0)
        self.textLock = Semaphore(0)
        self.intentLock = Semaphore(0)
        self.gestureLock = Semaphore(0)

        # Attributes of our application
        self.userName = None
        self.intendUnderstood = False

        # Pass the required Dialogflow parameters (add your Dialogflow parameters)
        self.setDialogflowKey('production_diagFl_key.json')
        self.setDialogflowAgent('sir-study-buddy-258913')
        # self.setDialogflowKey('sample_diagFl_key.json')
        # self.setDialogflowAgent('sir2019-g7-sample-wfkciw')

    def main(self):
        logger.debug('Main called...')
        # Setting language
        self.setLanguage('en-US')
        logger.debug('set language ran.')
        self.languageLock.acquire()
        self.say('Lock acquired. Running...')
        self.textLock.acquire()
        logger.debug('Lock acquired. Running...')
        try:
            self.ask('What\'s your name?', 'answer_name')
            self.sayAnimated('Oh hi ' + self.userName)
            self.textLock.acquire()
        except InteractionException:
            self.sayAnimated('Sorry, it was not possible to understand your name. I will go to standby mode now.')
            self.textLock.acquire()

    def onAudioIntent(self, *args, intentName):
        # Assuming we have a DialogueFlow app for the intent "answer_name"
        logger.warning(f'Arguments: {args}')
        logger.warning(f'Intent name: {intentName}')
        if intentName == 'answer_name':
            if len(args) > 0:
                self.intendUnderstood = True
                self.userName = args[0]

    def onRobotEvent(self, event):
        # make sure all our started actions are completed:
        if event == 'TextDone':
            self.textLock.release()
        elif event == 'LanguageChanged':
            self.languageLock.release()

        # log what is going on
        logger.debug(event)

    def ask(self, question, audioContext, attempts=3, timeout=5):
        # We only want the question to be asked once, right?
        self.sayAnimated(question)
        self.textLock.acquire()

        # new question, new stuff to understand
        self.intendUnderstood = False
        while attempts > 0 and not self.intendUnderstood:
            logger.debug(f'Attempts: {attempts}')
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
    logger.debug('Initialising the speech recognition app.')
    sample = SpeechRecogApp()
    try:
        # Run the application
        sample.main()
        sample.stop()
    except KeyboardInterrupt:
        logger.debug('Early stopping of thread.')
        try:
            sample.stop()
        except Exception as e:
            raise e

