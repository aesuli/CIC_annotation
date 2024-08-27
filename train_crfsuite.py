import datetime
import os
import pickle
from collections import Counter

import scipy
from sklearn.metrics import make_scorer
from sklearn.model_selection import RandomizedSearchCV
from sklearn_crfsuite import CRF, metrics
from sklearn_crfsuite.metrics import flat_classification_report

BOS = '__BOS__'
EOS = '__EOS__'


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
    features.extend(word_base_feats('w', w))

    window_size = 6
    ngram_max_size = 3

    seq = []
    for offset in range(-window_size, window_size + 1):
        if offset == 0:
            seq.append((0, 'w', w))
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
    return [label for token, label in sent]


def sent2tokens(sent):
    return [token for token, label in sent]


def main():
    with open('train_data.txt', mode='rt', encoding='utf-8') as input_file:
        train_sents = []
        sent = []
        for line in input_file:
            line = line.strip()
            if len(line) == 0 and len(sent) > 0:
                train_sents.append(sent)
                sent = []
            else:
                sent.append(line.split(' '))
        if len(sent) > 0:
            train_sents.append(sent)
        X_train = [sent2features(s) for s in train_sents]
        y_train = [sent2labels(s) for s in train_sents]

    labels = list(set([label for sent in y_train for label in sent])) #if label != 'O']))
    print(labels)

    crf = CRF(
        algorithm='lbfgs',
        max_iterations=500,
        all_possible_transitions=True,
        all_possible_states=True,
    )
    params_space = {
        'c1': scipy.stats.expon(scale=0.5),
        'c2': scipy.stats.expon(scale=0.05),
    }

    f1_scorer = make_scorer(metrics.flat_f1_score, average='micro', labels=labels)

    # search
    rs = RandomizedSearchCV(crf, params_space,
                            cv=5,
                            verbose=3,
                            n_jobs=os.cpu_count() // 2 - 1,
                            n_iter=100,
                            scoring=f1_scorer)

    rs.fit(X_train,y_train)

    model = rs.best_estimator_

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
    main()
