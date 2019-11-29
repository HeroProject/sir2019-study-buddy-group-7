import AbstractApplication as Base
from threading import Semaphore
from loguru import logger
import random
from textblob import TextBlob
import nltk
from datetime import datetime
import sys
import os
import json
from scheduler import make_schedule
from time import sleep

from emotion_wrapper import add_emotion

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
        self.language_lock = Semaphore(0)
        self.text_lock = Semaphore(0)
        self.intent_lock = Semaphore(0)
        self.gesture_lock = Semaphore(0)
        self.eye_lock = Semaphore(0)

        # Attributes of our application
        self.intent_understood = False
        self.activation = False
        self.student_feeling = None
        self.yes_answer = True
        # self.changing_wish = None
        # self.schedule = None
        self.hours_remaining = None
        self.hours_needed = None

        # Pass the required Dialogflow parameters (add your Dialogflow parameters)
        self.set_dialogflow_key('production_diagFl_key.json')
        self.set_dialogflow_agent('sir-study-buddy-258913')

        # Import data from config file
        try:
            with open('config/config.json', 'r') as cfile:
                self.config_data = json.load(cfile)
                self.questions = self.config_data['questions']
                self.responses = self.config_data['responses']
                logger.debug('Loaded JSON config')
        except Exception as e:
            logger.error(f'JSON loading failed with: {e}')
            raise e

    def main(self):
        # Setting language
        logger.info('Setting language')
        self.set_language('en-US')
        self.language_lock.acquire()
        # Robot gets activated
        logger.info('Activating Nao')
        self.set_non_idle()
        self.set_audio_hints(['study', 'buddy', 'robot', 'Nao'])
        self.say('Oh.')
        self.do_gesture('animations/Stand/Gestures/Hey_1')
        self.text_lock.acquire()
        self.gesture_lock.acquire()
        self.set_eye_color('white')
        self.eye_lock.acquire()

        # wait for activation
        while not self.activation:
            logger.info(f'activation: {self.activation}')
            self.set_audio_context('activation')
            self.start_listening()
            self.intent_lock.acquire(timeout=5)
            self.stop_listening()

        # Robot greets friendly and asks how student is doing
        logger.info('Asking about student feelings')
        self.ask(self.questions['students_feeling'], 'students_feeling', timeout=7, emotion='empathetic')

        # Let's fix the students anxiouseness!
        if self.student_is_anxious():
            # robot empathises and asks for time
            logger.info(
                'Empathising with anxious student and ask time remaining')
            self.set_eye_color('blue')
            self.eye_lock.acquire()
            self.ask(self.questions['time_left'], 'time_left', emotion='empathetic')
            logger.info(f'Student has {self.hours_remaining} remaining')
            self.say_animated(
                f'{self.hours_remaining}? With my help, that should be enough to get it all done!', emotion='happy')
            self.text_lock.acquire()

            # robot asks for the todos
            logger.info('Asking student for estimated workload')
            self.ask(self.questions['time_needed'], 'time_needed')

            # calculate the schedule and read it out loud
            schedule = self.compute_schedule(
                self.hours_remaining, self.hours_needed)
            logger.debug(f'Schedule: {schedule}')
            logger.info('Reading schedule...')
            self.say_animated(
                f"Here is your study schedule: {schedule}. I'll update you with the rest of the schedule later.")
            self.text_lock.acquire()
            # End conversation with motivational quote
            self.tell_random_quote()

        # Student seems to be doing fine (not anxious). No scheduling needed
        else:
            self.set_eye_color('yellow')
            self.eye_lock.acquire()
            self.ask(self.questions['extra_motivation'], 'yes_no', emotion='happy')
            if self.yes_answer:
                logger.info('Student requested motivation')
                self.tell_random_quote()
            else:
                self.say_animated('Okay. Good luck with your studies. You can ask me for help anytime!', emotion='happy')
                self.do_gesture('animations/Stand/Gestures/BowShort_1')
                self.text_lock.acquire()
                self.gesture_lock.acquire()

        logger.debug('Stopping')
        self.stop()

    def on_audio_intent(self, intent_name, *args):
        logger.debug(f'Audio intent: {intent_name}')
        logger.debug(f'Audio intent args: {args}')
        if intent_name is not None:
            self.intent_understood = True
            if intent_name == 'activation':
                self.activation = True
            elif intent_name == 'students_feeling' and len(args) > 0:
                self.student_feeling = list(args)
            elif intent_name == 'yes_no':
                if args[0] == 'yes':
                    self.yes_answer = True
                else:
                    self.yes_answer = False
            elif intent_name == 'time_left' and len(args) > 0:
                self.hours_remaining = args[0]
            elif intent_name == 'time_needed' and len(args) > 0:
                self.hours_needed = args[0]
            elif intent_name in ['changing_wish', 'schedule']:
                logger.error(f'Intent: {intent_name} not implemented.')
                raise NotImplementedError


    def on_robot_event(self, event):
        #TODO make sure all our started actions are completed
        if event == 'TextDone':
            self.text_lock.release()
        elif event == 'LanguageChanged':
            self.language_lock.release()
        elif event == 'GestureDone':
            self.gesture_lock.release()
        elif event == 'EyeColourDone':
            self.eye_lock.release()

    def ask(self, question, audioContext, attempts=3, timeout=5, emotion=None):
        # We only want the question to be asked once, right?
        self.say_animated(question, emotion=emotion)
        self.text_lock.acquire()
        # new question, new stuff to understand
        self.intent_understood = False
        while attempts > 0 and not self.intent_understood:
            logger.debug(f'Attempts {attempts}| audioContext {audioContext}')
            self.set_eye_color('white')
            self.eye_lock.acquire()
            attempts -= 1
            self.set_audio_context(audioContext)
            self.start_listening()
            self.intent_lock.acquire(timeout=timeout)
            self.stop_listening()
            if not self.intent_understood and attempts > 0:
                self.set_eye_color('red')
                self.say_animated(self.responses['please_repeat'])
                self.eye_lock.acquire()
                self.text_lock.acquire()

        if attempts == 0:
            self.say_animated(self.responses['repeat_timeout'])
            raise InteractionException

    def student_is_anxious(self):
        if len(self.student_feeling) == 0:
            logger.error(
                f'Could not retrieve student feelings to test anxiety.')
            raise InteractionException
        resp = self.student_feeling[0]
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

    def tell_random_quote(self):
        quotes = self.config_data['motivational_quotes']
        rndm_quote = quotes[random.randint(0, len(quotes) - 1)]
        self.say_animated('And never forget: ' + rndm_quote, emotion='happy')
        self.text_lock.acquire()

    def compute_schedule(self, timeLeft, timeNeeded, **kwargs):
        logger.info(
            f'Computing schedule for {timeNeeded}h work in {timeLeft}h time')
        sched = make_schedule(timeNeeded, timeLeft, **kwargs)
        return '. '.join(sched)


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
