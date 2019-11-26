import nltk.data


def add_emotion(str, emotion):
    '''
    Adding emotion tags to the robot's speech
    :param str: string of robot's speech
    :param emotion: string of emotions to express, can be 'happy', 'empathetic', tbc
    :return: new emotional string
    '''
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    sentences = tokenizer.tokenize(str)

    # '\\pau=500\\ pause in milliseconds
    #  \\vol=90\\ volume 0-100
    #  \\vct=90\\  voice pitch 50-200
    #  \\rspd=90\\'  speaking rate 50-400
    
    if emotion == 'happy':
        if len(sentences) > 1:
            return '\\vol=100\\\\vct=140\\\\rspd=120\\' + sentences[0] + '\\vol=100\\\\vct=120\\\\rspd=130\\' +\
                   ''.join(sentences[1:])
        return '\\vol=100\\' + '\\vct=150\\' + '\\rspd=150\\' + sentences[0]

    elif emotion == 'empathetic':
        if len(sentences) > 1:
            return '\\vol=80\\\\vct=80\\\\rspd=80\\' + sentences[0] + '\\pau=500\\\\vol=90\\\\vct=90\\\\rspd=90\\' +\
                   ''.join(sentences[1:])
    else:
        return str