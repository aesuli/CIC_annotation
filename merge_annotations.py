import os
import sys
from collections import defaultdict
from pathlib import Path


def main(dirs):
    annotations = defaultdict(list)
    for dirname in dirs:
        for file in Path(dirname).iterdir():
            file_annotations = list()
            with file.open(mode='rt',encoding='utf-8') as input_file:
                sequence = list()
                for line in input_file:
                    line= line.strip()
                    if len(line)==0:
                        file_annotations.append(sequence)
                        sequence=[]
                    else:
                        sequence.append(tuple(line.split(' ')))
                if len(sequence)>0:
                    file_annotations.append(sequence)
            if file.name in annotations:
                if len(annotations[file.name])!=len(file_annotations):
                    raise ValueError(f'Mismatched sentences count in file "{file.name}"')
                merged_annotations = list()
                for seq1,seq2 in zip(annotations[file.name],file_annotations):
                    merged_sequence = list()
                    if len(seq1) != len(seq2):
                        raise ValueError(f'Mismatched sentence length in file "{file.name}"')
                    for (t1,l1),(t2,l2) in zip(seq1,seq2):
                        if t1!=t2:
                            raise ValueError(f'Mismatched token ({t1}, {t2}) in file "{file.name}"')
                        if l1=='O':
                            merged_sequence.append((t1,l2))
                        else:
                            merged_sequence.append((t1,l1))
                    merged_annotations.append(merged_sequence)
                annotations[file.name] = merged_annotations
            else:
                annotations[file.name] = file_annotations
    out_dir = Path("annotations_merged")
    out_dir.mkdir(parents=True, exist_ok=True)
    for file_name, annotations in annotations.items():
        with (out_dir/file_name).open(mode='wt', encoding='utf-8') as output_file:
            for sequence in annotations:
                for token, label in sequence:
                    print(f'{token} {label}',file=output_file)
                print(file=output_file)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <dir_1> [<dir_2>+]")
        sys.exit(1)

    main(sys.argv[1:])