import datetime
import os
import pickle
import sys
from collections import Counter
from pprint import pprint

import scipy
from sklearn.metrics import make_scorer
from sklearn.model_selection import RandomizedSearchCV
from sklearn_crfsuite import CRF, metrics
from sklearn_crfsuite.metrics import flat_classification_report

from cas_to_bioes import read_cas_to_bioes, AnnotationState

BOS = '__BOS__'
EOS = '__EOS__'
NUM = '__NUM__'


def word_base_feats(prefix, w):
    if w == '__BOS__' or w == '__EOS__':
        return [f'{prefix}={w}']

    return [
        f'{prefix}={w}',
        f'{prefix}.lower={w.lower()}',
        f'{prefix}.isupper={w.isupper()}',
        f'{prefix}.istitle={w.istitle()}',
        f'{prefix}.isdigit={w.isdigit()}',
    ]


def word2features(sent, i):
    w = sent[i][0]
    features = [
        'bias',
    ]
    features.extend(word_base_feats('cw', w))

    window_size = 6
    ngram_max_size = 3

    seq = []
    for offset in range(-window_size, window_size + 1):
        if offset == 0:
            seq.append((0, 'cw', w))
        elif offset < 0:
            pw = BOS
            if i + offset >= 0:
                pw = sent[i + offset][0]
            seq.append((offset, f'pw{-offset}', pw))
        elif offset > 0:
            nw = EOS
            if i + offset < len(sent):
                nw = sent[i + offset][0]
            seq.append((offset, f'nw{offset}', nw))

    for offset, prefix, word in seq:
        if offset != 0:
            features.extend(word_base_feats(prefix, word))

    nums_to_label = []
    for off, feat, w in seq:
        if w.isdigit():
            nums_to_label.append((off, feat, NUM))
        else:
            nums_to_label.append((off, feat, w))

    seq = nums_to_label

    for n in range(2, ngram_max_size + 1):
        for i in range(len(seq) - n + 1):
            ngram = ', '.join([f'{prefix}={word}' for offset, prefix, word in seq[i:i + n]])
            features.append(f'{n}g=[{ngram}]')

    for n in range(1, ngram_max_size):
        for i in range(len(seq) - n + 1):
            if i < len(seq) // 2 - n:
                ngram = ', '.join([f'{prefix}={word}' for offset, prefix, word in seq[i:i + n]] +
                                  [f'{seq[len(seq) // 2][1]}={seq[len(seq) // 2][2]}'])
                features.append(f'{n + 1}g+=[{ngram}]')
            if i > len(seq) // 2 + 1:
                ngram = ', '.join([f'{seq[len(seq) // 2][1]}={seq[len(seq) // 2][2]}'] +
                                  [f'{prefix}={word}' for offset, prefix, word in seq[i:i + n]])
                features.append(f'{n + 1}g+=[{ngram}]')

    return features


def sent2features(sent):
    return [word2features(sent, i) for i in range(len(sent))]


def sent2labels(sent):
    return [label for token, begin, end, label in sent]


def sent2tokens(sent):
    return [token for token, begin, end, label in sent]


def main(tagged_files_filename, zip_file_path, username):
    with open(tagged_files_filename,mode='rt',encoding='utf-8') as input_file:
        file_list = [line.strip() for line in input_file]

    X_train = []
    y_train = []
    count =1
    for filename, _, annotations in read_cas_to_bioes(zip_file_path, username, AnnotationState.annotated):
        if filename[filename.find('annotation/')+len('annotation/'):filename.find(' ')] in file_list:
            print(filename, len(annotations))
            for sentence in annotations:
                for _,_,_,label in sentence:
                    if label.startswith('B') or label.startswith('S'):
                        count += 1
                X_train.append(sent2features(sentence))
                y_train.append(sent2labels(sentence))

    print(f'{count} annotations')

    labels = list(set([label for sent in y_train for label in sent]))
    print(labels)

    crf = CRF(
        algorithm='lbfgs',
        max_iterations=1000,
    )

    params_space = {
        'all_possible_transitions': [True, False],
        'all_possible_states': [True, False],
        'c1': scipy.stats.expon(scale=0.5),
        'c2': scipy.stats.expon(scale=0.05),
    }

    f1_scorer = make_scorer(metrics.flat_f1_score, average='macro', labels=labels)

    # search
    rs = RandomizedSearchCV(crf, params_space,
                            cv=5,
                            verbose=3,
                            n_jobs=os.cpu_count() // 2 - 1,
                            n_iter=100,
                            scoring=f1_scorer)

    rs.fit(X_train, y_train)

    pprint(rs.cv_results_)

    model = rs.best_estimator_

    pprint(model)

    model_name = f'ner-model_{datetime.datetime.now().isoformat()[:10]}.crfsuite.pkl'

    with open(model_name, mode='wb') as output_file:
        pickle.dump(model, output_file)

    y_pred = model.predict(X_train)

    print(flat_classification_report(y_train, y_pred, labels=labels, digits=3))

    info = model.tagger_.info()

    def print_transitions(trans_features):
        for (label_from, label_to), weight in trans_features:
            print("%-6s -> %-7s %0.6f" % (label_from, label_to, weight))

    print("Top likely transitions:")
    print_transitions(Counter(info.transitions).most_common(15))

    print("\nTop unlikely transitions:")
    print_transitions(Counter(info.transitions).most_common()[-15:])

    def print_state_features(state_features):
        for (attr, label), weight in state_features:
            print("%0.6f %-6s %s" % (weight, label, attr))

    print("Top positive:")
    print_state_features(Counter(info.state_features).most_common(20))

    print("\nTop negative:")
    print_state_features(Counter(info.state_features).most_common()[-20:])


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python script_name.py <tagged_files_filename> <zip_file_path> <username>")
        sys.exit(1)

    tagged_files_filename = sys.argv[1]
    zip_file_path = sys.argv[2]
    username = sys.argv[3]

    main(tagged_files_filename, zip_file_path, username)
