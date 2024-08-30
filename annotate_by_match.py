import os.path
import os.path
import sys
from collections import defaultdict
from pathlib import Path

from sklearn_crfsuite.metrics import flat_classification_report

from cas_to_bioes import read_cas_to_bioes, AnnotationState
from train_crfsuite import sent2tokens, sent2labels, NUM
from trie import Trie


def main(zip_file_path, username):
    annotated_spans = []
    pre_post_len = 3
    pre_spans = []
    post_spans = []
    for filename, annotations in read_cas_to_bioes(zip_file_path, username, AnnotationState.annotated):
        print(filename, len(annotations))
        for sentence in annotations:
            annotation = []
            pre = []
            post = ['*'] * (pre_post_len + 1)
            for token, label in sentence:
                if token.isdigit():
                    token = NUM
                if label != 'O':
                    if len(annotation) == 0:
                        pre_spans.append(tuple(pre))
                        pre = []
                    annotation.append(token)
                elif len(annotation) > 0:
                    annotated_spans.append(tuple(annotation))
                    annotation = []
                    post = []
                pre.append(token)
                if len(post) < pre_post_len:
                    post.append(token)
                elif len(post) == pre_post_len:
                    post_spans.append(tuple(post))
                    post.append('*')
                pre = pre[-pre_post_len:]
            if len(annotation) > 0:
                annotated_spans.append(tuple(annotation))

    annotation_trie = Trie(annotated_spans)
    pre_trie = Trie(pre_spans)
    post_trie = Trie(post_spans)

    X_test = defaultdict(list)
    X_test_num = defaultdict(list)
    y_test = defaultdict(list)
    for filename, annotations in read_cas_to_bioes(zip_file_path, username, AnnotationState.unannotated):
        for sentence in annotations:
            tokens = sent2tokens(sentence)
            tokens_num = [token if not token.isdigit() else NUM for token in tokens ]
            X_test[filename].append(tokens)
            X_test_num[filename].append(tokens_num)
            y_test[filename].append(sent2labels(sentence))

    y_pred = defaultdict(list)
    for filename, X_num in X_test_num.items():
        print(filename)
        for sentence_num in X_num:
            labels = ['O'] * len(sentence_num)
            for i in range(len(sentence_num)):
                matches = list(annotation_trie.prefix_matches(sentence_num[i:]))
                if len(matches) > 0:
                    labels[i] = 'B-AN'
                    for j in range(1, len(matches[-1][0]) - 1):
                        labels[i + j] = 'I-AN'
                    labels[i + len(matches[-1][0]) - 1] = 'E-AN'
                matches = list(pre_trie.prefix_matches(sentence_num[i:]))
                if len(matches) > 0:
                    if labels[i] == 'O':
                        labels[i] = 'PRE'
                    for j in range(1, len(matches[-1][0]) - 1):
                        if labels[i + j] == 'O':
                            labels[i + j] = 'PRE'
                    if labels[i + len(matches[-1][0]) - 1] == 'O':
                        labels[i + len(matches[-1][0]) - 1] = 'PRE'
                matches = list(post_trie.prefix_matches(sentence_num[i:]))
                if len(matches) > 0:
                    if labels[i] == 'O':
                        labels[i] = 'POST'
                    for j in range(1, len(matches[-1][0]) - 1):
                        if labels[i + j] == 'O':
                            labels[i + j] = 'POST'
                    if labels[i + len(matches[-1][0]) - 1] == 'O':
                        labels[i + len(matches[-1][0]) - 1] = 'POST'
            y_pred[filename].append(labels)

    output_dirname = 'annotations_by_match'
    os.makedirs(output_dirname, exist_ok=True)
    for filename, y in y_pred.items():
        with open(Path(output_dirname) / filename[filename.find('/') + 1:filename.rfind('/')], mode='wt',
                  encoding='utf-8') as output_file:
            for sent, labels in zip(X_test[filename], y):
                for word, label in zip(sent, labels):
                    print(f'{word} {label}', file=output_file)
                print(file=output_file)

    def dict_to_flat_list(dictionary):
        return [item for value in dictionary.values() for item in value]

    print(flat_classification_report(dict_to_flat_list(y_test), dict_to_flat_list(y_pred)))


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python script_name.py <zip_file_path> <username>")
        sys.exit(1)

    zip_file_path = sys.argv[1]
    username = sys.argv[2]
    main(zip_file_path, username)
