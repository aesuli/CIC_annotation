import datetime
from collections import Counter
from itertools import chain

import pycrfsuite
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelBinarizer

from train_crfsuite import sent2features, sent2labels, bio_classification_report


def main():
    with open('test_data.txt', mode='rt', encoding='utf-8') as input_file:
        test_sents = []
        sent = []
        for line in input_file:
            line = line.strip()
            if len(line) == 0 and len(sent) > 0:
                test_sents.append(sent)
                sent = []
            else:
                sent.append(line.split(' '))
        if len(sent) > 0:
            test_sents.append(sent)
        X_test = [sent2features(s) for s in test_sents]
        y_test = [sent2labels(s) for s in test_sents]

    model_name = f'ner-model_2024-08-26.crfsuite'

    tagger = pycrfsuite.Tagger()
    tagger.open(model_name)

    y_pred = []
    for xseq in X_test:
        labels = tagger.tag(xseq)
        y_pred.append(labels)
        for token, label in zip(xseq,labels):
            print(token[1][2:],label)
        print()

    # print(bio_classification_report(y_test, y_pred))


if __name__ == '__main__':
    main()
