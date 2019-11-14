import AbstractApplication as Base
from time import sleep

class SampleApplication(Base.AbstractApplication):
    def main(self):
        self.setLanguage('en-US')
        self.sayAnimated('Hello Group 7.')
        sleep(2)
        # test comment


    def onRobotEvent(self, event):
        print(event)

class DiagnosticApp(Base.AbstractApplication):
    def run(self):
        self.setLanguage('en-US')
        self.sayAnimated('Running diagnostics now.')
        sleep(2)
        '''
        self.say('Changing eye color')
        self.setEyeColour('red')
        sleep(4)
        self.setEyeColour('blue')
        sleep(1)
        '''
        self.say('Testing mobility.')
        sleep(2)
        self.doGesture('BowShort_1')
        #sleep(4)
        #self.say('Diagnostics complete.')


# Run the application
#sample = SampleApplication()
#sample.main()
#sample.stop()

diagnostic_app = DiagnosticApp()
diagnostic_app.run()
diagnostic_app.stop()
