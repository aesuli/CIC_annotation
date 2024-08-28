import pickle
import sys

from sklearn_crfsuite.metrics import flat_classification_report

from train_crfsuite import sent2features, sent2labels


def main():
    model_name = sys.argv[1]

    with open(model_name, mode='rb') as input_file:
        model = pickle.load(input_file)

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

    y_pred = model.predict(X_test)

    with open('test_data_annotated.txt',mode='wt',encoding='utf-8') as output_file:
        for sent,labels in zip(X_test,y_pred):
            for word, label in zip(sent,labels):
                print(f'{word[1][2:]} {label}', file=output_file)
            print(file=output_file)

    print(flat_classification_report(y_test, y_pred))


if __name__ == '__main__':
    main()
