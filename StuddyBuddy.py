import AbstractApplication as Base
from threading import Semaphore
from loguru import logger
import random
from textblob import TextBlob
import nltk
from datetime import datetime
import sys
import os

SETUP_MODE = False
LOGDIR = 'logs/'

if SETUP_MODE:
    logger.warning(f'Setup: Downloading nltk corpa...')
    try:
        nltk.download('punkt')
        logger.debug('Setup complete!')
    except Exception as e:
        logger.error(f'Setup failed with error: {e}')
        raise e


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
        self.studentsFeeling = None
        self.yesAnswer = True
        # self.changingWish = None
        # self.schedule = None
        self.timeLeft = None
        self.toDos = None

        # Pass the required Dialogflow parameters (add your Dialogflow parameters)
        self.setDialogflowKey('production_diagFl_key.json')
        self.setDialogflowAgent('sir-study-buddy-258913')

    def main(self):
        # Setting language
        logger.info('Setting language')
        self.setLanguage('en-US')
        self.languageLock.acquire()

        # Robot gets activated
        logger.info('Activating Nao')
        self.setAudioContext('activation')
        # wait for activation
        while not self.activation:
            self.startListening()
            logger.debug('Listening...')
            self.intentLock.acquire(timeout=5)
            self.stopListening()
            logger.debug('Not listening...')

        # Robot greets friendly and asks how student is doing
        logger.info('Asking about student feelings')
        self.ask('Hi! How are you?', 'students_feeling')

        # Let's fix the students anxiouseness!
        if self.studentIsAnxious():
            # robot empathises and asks for time
            logger.info(
                'Empathising with anxious student and ask time remaining')
            self.ask(
                'I am sorry to hear that. How many hours do you have left before your deadline?', 'time_left')
            logger.info(f'Student has {self.timeLeft} remaining')
            self.sayAnimated(
                f'{self.timeLeft}? With my help, that should be enough to get it all done!')
            self.textLock.acquire()

            # robot asks for the todos
            logger.info('Asking student for estimated workload')
            self.ask(
                'How many hours of studying do you think you still need to do to be prepared?', 'to_do')

            # calculate the schedule and read it out loud
            schedule = self.computeSchedule(self.timeLeft, self.toDos)
            self.sayAnimated(schedule)
            self.textLock.acquire()
            # leaving out the "sending email" and the "reschedule" part.

            # End conversation with motivational quote
            self.tellRandomMotivationQuote()

        # Student seems to be doing fine (not anxious). No scheduling needed
        else:
            # TODO: Configure yes_no intend in DialogFlow
            self.ask(
                'It seems like you are quite positive today. Do you still need any motivation?', 'yes_no')
            if self.yesAnswer:
                logger.info('Student requested motivation')
                self.tellRandomMotivationQuote()
        logger.debug('Stopping')
        self.stop()

    def onAudioIntent(self, *args, intentName):
        if len(args) > 0:
            self.intendUnderstood = True
            if intentName == 'activation':
                self.activation = True
            elif intentName == 'students_feeling':
                self.studentsFeeling = list(args)
            elif intentName == 'yes_no':
                if args[0] == 'yes':
                    self.yesAnswer = True
                else:
                    self.yesAnswer = False
            # elif intentName == 'changing_wish':
            #     pass
            # elif intentName == 'schedule':
            #     pass
            elif intentName == 'time_left':
                self.timeLeft = args[0]
            elif intentName == 'to_do':
                self.toDos = list(args)

    def onRobotEvent(self, event):
        """make sure all our started actions are completed"""
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
                self.sayAnimated(
                    'Sorry, I didn\'t catch that. Could you please repeat that?')
                self.textLock.acquire()
        if attempts == 0:
            self.sayAnimated(
                'Sorry. There seems to be a problem. I am shutting down.')
            raise InteractionException

    def studentIsAnxious(self):
        if len(self.studentsFeeling) == 0:
            logger.error(
                f'Could not retrieve student feelings text to test anxiety.')
            raise InteractionException
        resp = self.studentsFeeling
        logger.debug(f'Analysing sentiment of {resp}')
        sent = TextBlob(resp).sentiment
        polarity = sent.polarity
        subjectivity = sent.subjectivity
        logger.debug(f'Student polarity: {polarity}')
        logger.debug(f'Student subjectivity: {subjectivity}')
        if polarity < -0.0:
            logger.debug(f'Student classified as anxious')
            return True
        logger.info('Student NOT classified as anxious.')
        return False

    def tellRandomMotivationQuote(self):
        quotes = [
            'The will to win, the desire to succeed, the urge to reach your full potential. These are the keys that will unlock the door to personal excellence.',
            'Only you can change my life. No one can do it for you.',
            'With the new day comes new strength and new thoughts.',
            'Optimism is the faith that leads to achievement. Nothing can be done without hope and confidence.',
            'It does not matter how slowly you go as long as you do not stop.',
            'Sometimes later becomes never. Do it now.',
            'Great things never come from comfort zones.',
            'Success does not just find you. You have to go out and get it.']
        rndm_quote = quotes[random.randint(0, len(quotes) - 1)]
        self.sayAnimated('And never forget: ' + rndm_quote)
        self.textLock.acquire()

    def computeSchedule(self, timeLeft, toDos):
        # TODO: Implement this
        # Do the scheduling and return whatever can just be read out by the robot (=string).
        raise NotImplementedError


class InteractionException(Exception):
    def __init__(self):
        super().__init__()


if __name__ == '__main__':

    # Get current datetime stamp
    now = datetime.now().strftime("%m-%d-%H_%M_%S")

    # Configure logging to stderr at debug level
    logger.remove()
    logger.add(sys.stderr, level='DEBUG')

    # Configure logging to file at debug level
    if not os.path.exists(LOGDIR):
        os.makedirs(LOGDIR)
    logger.add("logs/{time}.log", level="DEBUG")

    # Initialise and run the application
    sample = StudyBuddyApp()
    try:
        # Run the application
        logger.warning('Running application...')
        sample.main()
    except KeyboardInterrupt:
        try:
            logger.warning('Keyboard interrupt. Stopping...')
            sample.stop()
        except Exception as e:
            logger.error(f'The interrupt shutdown process failed with: {e}')
            raise e
