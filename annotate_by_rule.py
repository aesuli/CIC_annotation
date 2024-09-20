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
from trie import Trie


def main(zip_file_path, username):
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

    rule_trie = Trie()

    rule_trie.insert([NUM,'.', 'q', '.',NUM,','])
    rule_trie.insert([NUM,'.','dist','.',','])
    max_end_dist = 10
    end_tokens = {'.', ',', ';'}

    y_pred = defaultdict(list)
    for filename, X_num in X_test_num.items():
        print(filename)
        for sentence_num in X_num:
            labels = ['O'] * len(sentence_num)
            for i in range(len(sentence_num)):
                matches = list(rule_trie.prefix_matches(sentence_num[i:]))
                for match in matches:
                    offset = i+len(match[0])
                    end_idx = None
                    for j in range(offset,min(offset+max_end_dist,len(sentence_num))):
                        if sentence_num[j] in end_tokens:
                            end_idx = j-1
                            break
                    if end_idx:
                        labels[i] = 'RULE|B-AN'
                        for j in range(i+1, end_idx):
                            labels[j] = 'RULE|I-AN'
                        labels[end_idx] = 'RULE|E-AN'
            y_pred[filename].append(labels)

    output_dirname = 'annotations_by_rule'
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

    def dict_to_flat_list(dictionary):
        return [item for value in dictionary.values() for item in value]

    print(flat_classification_report(dict_to_flat_list(y_test), dict_to_flat_list(y_pred)))


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python script_name.py <zip_file_path> <username>")
        sys.exit(1)

    zip_filename = sys.argv[1]
    username = sys.argv[2]
    main(zip_filename, username)
