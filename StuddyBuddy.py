import AbstractApplication as Base
from threading import Semaphore
# from loguru import logger
import random


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
        self.changingWish = None
        self.schedule = None
        self.timeLeft = None
        self.toDos = None

        # Pass the required Dialogflow parameters (add your Dialogflow parameters)
        self.setDialogflowKey('production_diagFl_key.json')
        self.setDialogflowAgent('sir-study-buddy-258913')

    def main(self):
        # Setting language
        self.setLanguage('en-US')
        self.languageLock.acquire()

        # Robot gets activated
        self.setAudioContext('activation')
        # wait for activation
        while not self.activation:
            self.startListening()
            self.intentLock.acquire(timeout=5)
            self.stopListening()

        # Robot greets friendly and asks how student is doing
        self.ask('Hi! How are you?', 'students_feeling')

        # Let's fix the students anxiouseness!
        if self.studentIsAnxious():
            # robot amphazises and asks for time
            self.ask('I am sorry to hear that. How much time do you have left for studying?', 'time_left')
            self.sayAnimated(self.timeLeft + '? That is quite a lot.')
            self.textLock.acquire()

            # robot asks for the todos
            self.ask('What are your to do\'s and how long do you think will each of them take?', 'to_do')

            # calculate the schedule and read it out loud
            schedule = self.computeSchedule(self.timeLeft, self.toDos)
            self.sayAnimated(schedule)
            self.textLock.acquire()
            # leaving out the "sending email" part here.


        # Student seems to be doing fine (not anxious). No scheduling needed
        else:
            # TODO: Configure yes_no intend in DialogFlow
            self.ask('It seems like you are quite positive today. Do you still need any motivation?', 'yes_no')
            if self.yesAnswer:
                self.tellRandomMotivationQuote()
            else:
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
            elif intentName == 'changing_wish':
                pass
            elif intentName == 'schedule':
                pass
            elif intentName == 'time_left':
                self.timeLeft = args[0]
            elif intentName == 'to_do':
                self.toDos = list(args)

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
            self.sayAnimated('Sorry. There seems to be a problem. I am shutting down.')
            raise InteractionException

    def studentIsAnxious(self):
        # TODO: implement this
        # Here, we want to do the sentiment analysis
        raise NotImplementedError

    def tellRandomMotivationQuote(self):
        quotes = ['The will to win, the desire to succeed, the urge to reach your full potential.Tthese are the keys that will unlock the door to personal excellence.',
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
        self.stop()

    def computeSchedule(self, timeLeft, toDos):
        # TODO: Implement this
        # Do the scheduling and return whatever can just be read out by the robot (=string).
        raise NotImplementedError


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