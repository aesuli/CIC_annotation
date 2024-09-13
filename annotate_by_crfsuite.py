import os
import pickle
import sys
from collections import defaultdict
from pathlib import Path

from sklearn_crfsuite.metrics import flat_classification_report

from cas_to_bioes import read_cas_to_bioes, AnnotationState
from train_crfsuite import sent2features, sent2labels


def main(model_filename, zip_file_path, username):
    with open(model_filename, mode='rb') as input_file:
        model = pickle.load(input_file)

    X_test = defaultdict(list)
    X_test_features = defaultdict(list)
    y_test = defaultdict(list)
    texts = dict()
    for filename, text, annotations in read_cas_to_bioes(zip_file_path, username, AnnotationState.any):
        print(filename, len(annotations))
        texts[filename] = text
        for sentence in annotations:
            X_test[filename].append([(token, start, end) for token, start, end, _ in sentence])
            X_test_features[filename].append(sent2features(sentence))
            y_test[filename].append(sent2labels(sentence))

    y_pred = defaultdict(list)
    for filename, X in X_test_features.items():
        print(filename)
        y_pred[filename] = model.predict(X)

    output_dirname = 'annotations_crfsuite'
    os.makedirs(output_dirname, exist_ok=True)
    for filename, y in y_pred.items():
        with open(Path(output_dirname) / filename[filename.find('/') + 1:filename.rfind('/')], mode='wt',
                  encoding='utf-8') as output_file:
            print(texts[filename],file=output_file, end='')
        with open(Path(output_dirname) / (filename[filename.find('/') + 1:filename.rfind('/')]+'.bioes'), mode='wt',
                  encoding='utf-8') as output_file:
            for sent, labels in zip(X_test[filename], y):
                for (word, start, end), label in zip(sent, labels):
                    if label == 'O':
                        print(f'{word} {start} {end} {label}', file=output_file)
                    else:
                        print(f'{word} {start} {end} CRF|{label}', file=output_file)
                print(file=output_file)

    def dict_to_flat_list(dictionary):
        return [item for value in dictionary.values() for item in value]

    print(flat_classification_report(dict_to_flat_list(y_test), dict_to_flat_list(y_pred)))


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python script_name.py <model_file_path> <zip_file_path> <username>")
        sys.exit(1)

    model_filename = sys.argv[1]
    zip_filename = sys.argv[2]
    username = sys.argv[3]
    main(model_filename, zip_filename, username)
