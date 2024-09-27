import sys
from collections import Counter, defaultdict
from pathlib import Path

import cassis


def main(source_dir, output_file, mark_source=False):

    source_dir = Path(source_dir)

    stats = Counter()
    by_file_stats = defaultdict(Counter)

    for file_source in source_dir.glob('*.bioes'):
        with file_source.open(mode='rt', encoding='utf-8') as input_file:
            last_label = 'O'
            last_end = -1
            annotation_start = -1
            annotation_type = None
            for line in input_file:
                line = line.strip()
                if len(line) > 0:
                    token, start, end, label = line.split(' ')
                    if annotation_type is not None and not label.endswith(annotation_type) and last_label.endswith(annotation_type):
                        if annotation_type=='AN':
                            if mark_source:
                                source = last_label.split('|')[0]
                                stats.update([f'Allegazione normativa|{source}'])
                                by_file_stats[file_source].update([f'Allegazione normativa|{source}'])
                            else:
                                stats.update(['Allegazione normativa'])
                                by_file_stats[file_source].update(['Allegazione normativa'])
                        elif annotation_type=='LEMMA':
                            stats.update(['Lemma glossato'])
                            by_file_stats[file_source].update(['Lemma glossato'])
                        else:
                            raise ValueError(f'Unknown annotation type {annotation_type}')
                        annotation_start = -1
                        annotation_type = None
                    elif label.endswith('AN') and last_label == 'O':
                        annotation_start = start
                        annotation_type = 'AN'
                    elif label.endswith('LEMMA') and last_label == 'O':
                        annotation_start = start
                        annotation_type = 'LEMMA'

                    last_end = end

                    if label.endswith('AN') or label.endswith('LEMMA'):
                        last_label = label
                    else:
                        last_label = 'O'
                else:
                    if annotation_type is not None and last_label.endswith(annotation_type):
                        if annotation_type=='AN':
                            if mark_source:
                                source = last_label.split('|')[0]
                                stats.update([f'Allegazione normativa|{source}'])
                                by_file_stats[file_source].update([f'Allegazione normativa|{source}'])
                            else:
                                stats.update(['Allegazione normativa'])
                                by_file_stats[file_source].update(['Allegazione normativa'])
                        elif annotation_type=='LEMMA':
                            stats.update(['Lemma glossato'])
                            by_file_stats[file_source].update(['Lemma glossato'])
                        else:
                            raise ValueError(f'Unknown annotation type {annotation_type}')

                    last_label = 'O'
                    last_end = -1
                    annotation_start = -1
                    annotation_type = None

    print('## Global statistics',file=output_file)
    print(file=output_file)
    print('| TYPE |  COUNT |',file=output_file)
    print('|:-----|-------:|',file=output_file)
    for key in stats:
        print(f'| {key.replace("|","&#124;"):30} | {stats[key]:10d} |',file=output_file)
    print(file=output_file)

    print(f"Number of documents: {len(by_file_stats):10d}",file=output_file)
    print(file=output_file)

    print('| TYPE |  AVERAGE |',file=output_file)
    print('|:-----|-------:|',file=output_file)
    for key in stats:
        print(f'| {key.replace("|","&#124;"):30} | {(stats[key]/len(by_file_stats)):5.1f} |',file=output_file)
    print(file=output_file)

    print('## By document statistics',file=output_file)
    for filename in by_file_stats:
        print(Path(filename).name.replace(".txt.bioes",""),file=output_file)
        print(file=output_file)
        print('| TYPE |  COUNT |',file=output_file)
        print('|:-----|-------:|',file=output_file)
        for key in by_file_stats[filename]:
            print(f'| {key.replace("|","&#124;"):30} | {by_file_stats[filename][key]:10d} |',file=output_file)
        print(file=output_file)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <source_dir>")
        sys.exit(1)

    source_dir = sys.argv[1]
    
    with open(f'stats_{Path(source_dir).name}.md',mode='wt',encoding='utf-8') as output_file:
        print('# Plain stats',file=output_file)
        main(source_dir, output_file)
        print(file=output_file)
        print('# By source stats',file=output_file)
        main(source_dir, output_file,True)
