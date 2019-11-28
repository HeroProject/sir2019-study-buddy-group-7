import nltk.data


def add_emotion(str, emotion):
    '''
    Adding emotion tags to the robot's speech
    :param str: string of robot's speech
    :param emotion: string of emotions to express, can be 'happy', 'empathetic', tbc
    :return: new emotional string
    '''
    # tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    # sentences = tokenizer.tokenize(str)

    # '\pau=500\ pause in milliseconds
    #  \vol=90\ volume 0-100
    #  \vct=90\  voice pitch 50-200
    #  \rspd=90\'  speaking rate 50-400

    if emotion == 'happy':
        return '\\vol=90\\\\vct=110\\\\rspd=110\\' + str

    elif emotion == 'empathetic':
        return '\\vol=70\\\\vct=80\\\\rspd=80\\' + str