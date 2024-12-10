import sys
from collections import defaultdict
from pathlib import Path


def main(dirname):
    annotations = defaultdict(list)
    texts = dict()
    count = 0
    for file in Path(dirname).glob('*.bioes'):
        file_annotations = list()
        with file.open(mode='rt', encoding='utf-8') as input_file:
            sequence = list()
            for line in input_file:
                line = line.strip()
                if len(line) == 0:
                    file_annotations.append(sequence)
                    sequence = []
                else:
                    sequence.append(tuple(line.split(' ')))
            if len(sequence) > 0:
                file_annotations.append(sequence)

        postprocessed_annotations = list()
        for seq in file_annotations:
            postprocessed_sequence = list()
            for i,(t, s, e, l) in enumerate(seq):
                if t=="ff" and '|' not in l and seq[i+1][0]=='.' and seq[i+2][-1].endswith('B-AN'):
                    l = seq[i+2][-1]
                    lb = l.replace('B-AN','I-AN')
                    seq[i+1] = (seq[i+1][0],seq[i+1][1],seq[i+1][2],lb)
                    seq[i+2] = (seq[i+2][0],seq[i+2][1],seq[i+2][2],lb)
                    count +=1
                postprocessed_sequence.append((t, s, e, l))
            postprocessed_annotations.append(postprocessed_sequence)
        annotations[file.name] = postprocessed_annotations
        text_filename = file.name[:-len('.bioes')]
        with open(Path(dirname)/text_filename,mode='rt',encoding='utf-8') as input_file:
            texts[text_filename] = input_file.read()
    print(count)

    out_dir = Path("annotations_postprocessed")
    out_dir.mkdir(parents=True, exist_ok=True)
    for file_name, text in texts.items():
        with (out_dir / file_name).open(mode='wt', encoding='utf-8') as output_file:
            print(text,file=output_file, end='')
    for file_name, annotations in annotations.items():
        with (out_dir / file_name).open(mode='wt', encoding='utf-8') as output_file:
            for sequence in annotations:
                for token, start, end, label in sequence:
                    print(f'{token} {start} {end} {label}', file=output_file)
                print(file=output_file)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python script_name.py <dir>")
        sys.exit(1)

    main(sys.argv[1])
