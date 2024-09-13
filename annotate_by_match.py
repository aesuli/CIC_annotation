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


def main(model_filename, zip_file_path, username):
    with open(model_filename, mode='rb') as input_file:
        annotation_trie = pickle.load(input_file)
        pre_trie = pickle.load(input_file)
        post_trie = pickle.load(input_file)
        stats = pickle.load(input_file)

    X_test = defaultdict(list)
    X_test_num = defaultdict(list)
    y_test = defaultdict(list)
    texts = dict()
    for filename, text, annotations in read_cas_to_bioes(zip_file_path, username, AnnotationState.any):
        texts[filename] = text
        for sentence in annotations:
            X_test[filename].append([(token, start, end) for token, start, end, _ in sentence])
            X_test_num[filename].append([token if not token.isdigit() else NUM for token in sent2tokens(sentence)])
            y_test[filename].append(sent2labels(sentence))

    min_pre_post_count = 10

    y_pred = defaultdict(list)
    for filename, X_num in X_test_num.items():
        print(filename)
        for sentence_num in X_num:
            labels = ['O'] * len(sentence_num)
            for i in range(len(sentence_num)):
                matches = list(annotation_trie.prefix_matches(sentence_num[i:]))
                if len(matches) > 0:
                    labels[i] = 'MATCH|B-AN'
                    for j in range(1, len(matches[-1][0]) - 1):
                        labels[i + j] = 'MATCH|I-AN'
                    labels[i + len(matches[-1][0]) - 1] = 'MATCH|E-AN'
                matches = list(pre_trie.prefix_matches(sentence_num[i:]))
                if len(matches) > 0 and matches[0][1] > min_pre_post_count:
                    if labels[i] == 'O':
                        labels[i] = 'PRE'
                    for j in range(1, len(matches[-1][0]) - 1):
                        if labels[i + j] == 'O':
                            labels[i + j] = 'PRE'
                    if labels[i + len(matches[-1][0]) - 1] == 'O':
                        labels[i + len(matches[-1][0]) - 1] = 'PRE'
                matches = list(post_trie.prefix_matches(sentence_num[i:]))
                if len(matches) > 0 and matches[0][1] > min_pre_post_count:
                    if labels[i] == 'O':
                        labels[i] = 'POST'
                    for j in range(1, len(matches[-1][0]) - 1):
                        if labels[i + j] == 'O':
                            labels[i + j] = 'POST'
                    if labels[i + len(matches[-1][0]) - 1] == 'O':
                        labels[i + len(matches[-1][0]) - 1] = 'POST'
            y_pred[filename].append(labels)

    den = 0
    num = 0
    squares = 0
    for value, freq in stats.items():
        den += freq
        partial = value * freq
        num += partial
        squares += partial * value
    mean = num / den
    variance = (squares / den) - (mean * mean)
    std_dev = math.sqrt(variance)
    print(mean, std_dev)

    for filename, annotations in y_pred.items():
        for w, sentence in enumerate(annotations):
            for i in range(len(sentence)):
                if sentence[i] == 'PRE':
                    j = i + 1
                    while j < len(sentence) and sentence[j] == 'O' and j - i < mean + std_dev * 2:
                        j += 1
                    if mean - std_dev * 2 < j - i < mean + std_dev * 2 and j < len(sentence) and sentence[j] == 'POST':
                        if j - i - 1 == 1:
                            sentence[i + 1] = 'PREPOST|S-AN'
                        if j - i - 1 > 1:
                            sentence[i + 1] = 'PREPOST|B-AN'
                            sentence[j - 1] = 'PREPOST|E-AN'
                            for k in range(i + 2, j - 1):
                                sentence[k] = 'PREPOST|I-AN'

    output_dirname = 'annotations_by_match'
    os.makedirs(output_dirname, exist_ok=True)
    for filename, y in y_pred.items():
        with (Path(output_dirname) / filename[filename.find('/') + 1:filename.rfind('/')]).open(mode='wt',
                                                                                                encoding='utf-8') as output_file:
            print(texts[filename], file=output_file, end='')
        with (Path(output_dirname) / (filename[filename.find('/') + 1:filename.rfind('/')] + '.bioes')).open(mode='wt',
                                                                                                             encoding='utf-8') as output_file:
            for sent, labels in zip(X_test[filename], y):
                for (word, start, end), label in zip(sent, labels):
                    print(f'{word} {start} {end} {label}', file=output_file)
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
