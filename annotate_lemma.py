import math
import os.path
import os.path
import pickle
import sys
from collections import defaultdict
from pathlib import Path

from sklearn_crfsuite.metrics import flat_classification_report

from cas_to_bioes import read_cas_to_bioes, AnnotationState
from train_crfsuite import sent2tokens, sent2labels, NUM


def main(lemma_file_path, zip_file_path, username):
    with open(lemma_file_path,mode='rt', encoding='utf-8') as input_file:
        lemmas = [lemma.strip() for lemma in input_file.readlines()]
    lemmas.reverse()

    X_test = defaultdict(list)
    y_test = defaultdict(list)
    texts = dict()
    for filename, text, annotations in read_cas_to_bioes(zip_file_path, username, AnnotationState.any):
        texts[filename] = text
        for sentence in annotations:
            X_test[filename].append([(token, start, end) for token, start, end, _ in sentence])
            y_test[filename].append(sent2labels(sentence))

    y_pred = defaultdict(list)
    next_lemma = lemmas.pop()
    sorted_files = list(sorted(X_test.items()))
    first_file = sorted_files[-1]
    sorted_files = [first_file]+sorted_files[:-1]
    for filename, X in sorted_files:
        print(filename)
        for sentence in X:
            labels = ['O'] * len(sentence)
            in_lemma = False
            start_lemma = -1
            if next_lemma:
                for i in range(len(sentence)):
                    token, start, end = sentence[i]
                    if not in_lemma:
                        if next_lemma.startswith(token):
                            if texts[filename][start-1]==' ' and texts[filename][start-2]=='\n':
                                in_lemma = True
                                start_lemma = i
                    if in_lemma and next_lemma.endswith(token):
                        if i-start_lemma==0:
                            labels[i] = 'S-LEMMA'
                        else:
                            labels[start_lemma] = 'B-LEMMA'
                            for j in range(start_lemma+1, i):
                                labels[j] = 'I-LEMMA'
                            labels[i] = 'E-LEMMA'
                        in_lemma = False
                        start_lemma = -1
                        try:
                            next_lemma = lemmas.pop()
                        except:
                            print('*** END ***')
                            next_lemma = None
            y_pred[filename].append(labels)


    output_dirname = 'annotations_lemma'
    os.makedirs(output_dirname, exist_ok=True)
    for filename, y in y_pred.items():
        with (Path(output_dirname) / filename[filename.find('/') + 1:filename.rfind('/')]).open(mode='wt',
                                                                                                encoding='utf-8') as output_file:
            print(texts[filename].replace('\r',''), file=output_file, end='')
        with (Path(output_dirname) / (filename[filename.find('/') + 1:filename.rfind('/')] + '.bioes')).open(mode='wt',
                                                                                                             encoding='utf-8') as output_file:
            for sent, labels in zip(X_test[filename], y):
                for (word, start, end), label in zip(sent, labels):
                    print(f'{word} {start} {end} {label}', file=output_file)
                print(file=output_file)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python script_name.py <lemma_file_path> <zip_file_path> <username> ")
        sys.exit(1)

    lemma_file_path = sys.argv[1]
    zip_filename = sys.argv[2]
    username = sys.argv[3]
    main(lemma_file_path, zip_filename, username)
