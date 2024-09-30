import datetime
import os
import pickle
import sys
from collections import Counter
from pathlib import Path

from cas_to_bioes import read_cas_to_bioes, AnnotationState
from train_crfsuite import NUM
from trie import Trie


def main(zip_file_path, username):
    annotated_spans = []
    pre_post_len = 3
    pre_spans = []
    post_spans = []
    stats = Counter()
    for filename, _, annotations in read_cas_to_bioes(zip_file_path, username, AnnotationState.annotated):
        print(filename, len(annotations))
        for sentence in annotations:
            annotation = []
            pre = []
            post = ['*'] * (pre_post_len + 1)
            for token, begin, end, label in sentence:
                if token.isdigit():
                    token = NUM
                if label != 'O':
                    if len(annotation) == 0:
                        pre_spans.append(tuple(pre))
                        pre = []
                    annotation.append(token)
                elif len(annotation) > 0:
                    annotated_spans.append(tuple(annotation))
                    stats.update([len(annotation)])
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

    model_name = f'match-model_{datetime.datetime.now().isoformat()[:10]}.pkl'

    with open(model_name, mode='wb') as output_file:
        pickle.dump(annotation_trie, output_file)
        pickle.dump(pre_trie, output_file)
        pickle.dump(post_trie, output_file)
        pickle.dump(stats, output_file)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python script_name.py <zip_file_path> <username>")
        sys.exit(1)

    zip_file_path = sys.argv[1]
    username = sys.argv[2]
    main(zip_file_path, username)
