import os.path
import os.path
import os.path
import re
import sys
from collections import defaultdict
from pathlib import Path

from cas_to_bioes import read_cas_to_bioes, AnnotationState
from train_crfsuite import sent2labels


def main(zip_file_path, username):
    X_test = defaultdict(list)
    y_test = defaultdict(list)
    texts = dict()
    for filename, text, annotations in read_cas_to_bioes(zip_file_path, username, AnnotationState.any):
        texts[filename] = text
        for sentence in annotations:
            X_test[filename].append([(token, start, end) for token, start, end, _ in sentence])
            y_test[filename].append(sent2labels(sentence))

    y_pred = defaultdict(list)
    sorted_files = list(sorted(X_test.items()))
    first_file = sorted_files[-1]
    sorted_files = [first_file] + sorted_files[:-1]
    for filename, X in sorted_files:
        print(filename)
        for sentence in X:
            labels = ['O'] * len(sentence)
            in_chapter = False
            for i in range(len(sentence)):
                token, start, end = sentence[i]
                if not in_chapter:
                    if token == 'X':
                        in_chapter = True
                elif in_chapter:
                    if re.match('([0-9]+\.[0-9]+\.[0-9]+)', token):
                        labels[i] = 'B-CHAPTER'
                        for j in range(i+1,len(sentence)):
                            if sentence[j][0]=='':
                                j-=1
                                break
                        for k in range(i+1,j):
                            labels[k]= 'I-CHAPTER'
                        labels[j] = 'E-CHAPTER'
                        print(' '.join([t[0] for t in sentence[i:j+1]]))
                    in_chapter = False
            y_pred[filename].append(labels)

    output_dirname = 'annotations_chapter'
    os.makedirs(output_dirname, exist_ok=True)
    for filename, y in y_pred.items():
        with (Path(output_dirname) / filename[filename.find('/') + 1:filename.rfind('/')]).open(mode='wt',
                                                                                                encoding='utf-8') as output_file:
            print(texts[filename].replace('\r', ''), file=output_file, end='')
        with (Path(output_dirname) / (filename[filename.find('/') + 1:filename.rfind('/')] + '.bioes')).open(mode='wt',
                                                                                                             encoding='utf-8') as output_file:
            for sent, labels in zip(X_test[filename], y):
                for (word, start, end), label in zip(sent, labels):
                    print(f'{word} {start} {end} {label}', file=output_file)
                print(file=output_file)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python script_name.py <zip_file_path> <username> ")
        sys.exit(1)

    zip_filename = sys.argv[1]
    username = sys.argv[2]
    main(zip_filename, username)
