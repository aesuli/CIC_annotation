import sys
from collections import defaultdict
from pathlib import Path

import cassis

# https://colab.research.google.com/github/inception-project/inception/blob/main/notebooks/annotated_word_files_to_cas_xmi.ipynb#scrollTo=UlrkckjkLzBc

typesystem_content = '''<?xml version="1.0" encoding="UTF-8"?>
<typeSystemDescription xmlns="http://uima.apache.org/resourceSpecifier">
    <types>
        <typeDescription>
            <name>webanno.custom.Glossa</name>
            <description/>
            <supertypeName>uima.tcas.Annotation</supertypeName>
            <features>
                <featureDescription>
                    <name>Tipo</name>
                    <description/>
                    <rangeTypeName>uima.cas.String</rangeTypeName>
                </featureDescription>
            </features>
        </typeDescription>
    </types>
</typeSystemDescription>
'''


def main(source_dir, output_filename):
    typesystem = cassis.load_typesystem(typesystem_content)

    index = defaultdict(lambda: defaultdict(list))
    source_dir = Path(source_dir)
    for file_source in source_dir.glob('*.xmi'):
        capitolo = '0.00.00'
        with (file_source.open(mode='rt', encoding='utf-8') as input_file):
            titolo = file_source.name[file_source.name.find('\\') + 1:file_source.name.rfind('.')].strip()
            cas = cassis.load_cas_from_xmi(file_source, typesystem)
            lemma = None
            for annotation in cas.select_all():
                if annotation.Tipo == 'Allegazione normativa':
                    annotation_text = annotation.get_covered_text()
                    first_comma = annotation_text.find(',')
                    first_paragraph = annotation_text.find('§')
                    if first_comma == -1:
                        first_comma = len(annotation_text)
                    if first_paragraph == -1:
                        first_paragraph = len(annotation_text)
                    split = min(first_comma, first_paragraph)
                    book = annotation_text[:split]
                    if book.startswith('.'):
                        book = book[1:]
                    book = book.strip()
                    if len(book)==0:
                        continue
                    article = annotation_text[split + 1:].strip()
                    while len(article)>0 and article[-1] in (',','.',';'):
                        article = article[:-1].strip()
                    index[book][article].append((titolo, capitolo, lemma))
                elif annotation.Tipo == 'Lemma glossato':
                    lemma = annotation.get_covered_text()
                elif annotation.Tipo == 'Capitolo':
                    capitolo = annotation.get_covered_text()
                elif annotation.Tipo == 'Titolo':
                    ann_titolo = annotation.get_covered_text()
                    if ann_titolo!=titolo:
                        raise ValueError(f'Mismatched annotation in {file_source}: {annotation}')
                else:
                    raise ValueError(f'Unknown annotation in {file_source}: {annotation}')

    print(f'#books {len(index)}')
    print(f'#articles {sum([len(v) for v in index.values()])}')

    with open(output_filename, mode='wt', encoding='utf-8') as output_file:
        for book in sorted(index):
            for article in sorted(index[book]):
                for titolo, capitolo, lemma in sorted(index[book][article], key=lambda x: x[1]):
                    print(book, article, titolo, capitolo, lemma, sep='\t', file=output_file)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python script_name.py <source_dir> <output_filename>")
        sys.exit(1)

    source_dir = sys.argv[1]
    output_filename = sys.argv[2]
    main(source_dir, output_filename)
