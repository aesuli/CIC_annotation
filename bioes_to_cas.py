import sys
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


def main(source_dir, target_dir, mark_source=False):
    target_dir = Path(target_dir)

    target_dir.mkdir(parents=True, exist_ok=True)

    typesystem = cassis.load_typesystem(typesystem_content)
    GlossaAnnotation = typesystem.get_type("webanno.custom.Glossa")

    source_dir = Path(source_dir)

    for file_source, file_text in zip(source_dir.glob('*.bioes'), source_dir.glob('*.txt')):
        with (file_source.open(mode='rt', encoding='utf-8') as input_file,
              file_text.open(mode='rt', encoding='utf-8') as text_file):
            cas = cassis.Cas(typesystem)
            text = text_file.read()
            text = text.replace('\n', '\r\n')
            cas.sofa_string = text
            cas.sofa_mime = 'text'
            last_label = 'O'
            last_end = -1
            annotation_start = -1
            annotation_type = None
            for line in input_file:
                line = line.strip()
                if len(line) > 0:
                    token, start, end, label = line.split(' ')
                    if annotation_type is not None and not label.endswith(annotation_type) and last_label.endswith(
                            annotation_type):
                        if annotation_type == 'AN':
                            if mark_source:
                                source = last_label.split('|')[0]
                                glossa = GlossaAnnotation(begin=int(annotation_start), end=int(last_end),
                                                          Tipo=f'Allegazione normativa|{source}')
                            else:
                                glossa = GlossaAnnotation(begin=int(annotation_start), end=int(last_end),
                                                          Tipo='Allegazione normativa')
                        elif annotation_type == 'LEMMA':
                            glossa = GlossaAnnotation(begin=int(annotation_start), end=int(last_end),
                                                      Tipo='Lemma glossato')
                        elif annotation_type == 'CHAPTER':
                            glossa = GlossaAnnotation(begin=int(annotation_start), end=int(last_end),
                                                      Tipo='Capitolo')
                        elif annotation_type == 'TITLE':
                            glossa = GlossaAnnotation(begin=int(annotation_start), end=int(last_end),
                                                      Tipo='Titolo')
                        else:
                            raise ValueError(f'Unknown annotation type {annotation_type}')
                        cas.add(glossa)
                        annotation_start = -1
                        annotation_type = None
                    elif label.endswith('AN') and last_label == 'O':
                        annotation_start = start
                        annotation_type = 'AN'
                    elif label.endswith('LEMMA') and last_label == 'O':
                        annotation_start = start
                        annotation_type = 'LEMMA'
                    elif label.endswith('CHAPTER') and last_label == 'O':
                        annotation_start = start
                        annotation_type = 'CHAPTER'
                    elif label.endswith('TITLE') and last_label == 'O':
                        annotation_start = start
                        annotation_type = 'TITLE'

                    last_end = end

                    if label.endswith('AN') or label.endswith('LEMMA') or label.endswith('CHAPTER') or label.endswith(
                            'TITLE'):
                        last_label = label
                    else:
                        last_label = 'O'
                else:
                    if annotation_type is not None and last_label.endswith(annotation_type):
                        if annotation_type == 'AN':
                            if mark_source:
                                source = last_label.split('|')[0]
                                glossa = GlossaAnnotation(begin=int(annotation_start), end=int(last_end),
                                                          Tipo=f'Allegazione normativa|{source}')
                            else:
                                glossa = GlossaAnnotation(begin=int(annotation_start), end=int(last_end),
                                                          Tipo='Allegazione normativa')
                        elif annotation_type == 'LEMMA':
                            glossa = GlossaAnnotation(begin=int(annotation_start), end=int(last_end),
                                                      Tipo='Lemma glossato')
                        elif annotation_type == 'CHAPTER':
                            glossa = GlossaAnnotation(begin=int(annotation_start), end=int(last_end),
                                                      Tipo='Capitolo')
                        elif annotation_type == 'TITLE':
                            glossa = GlossaAnnotation(begin=int(annotation_start), end=int(last_end),
                                                      Tipo='Titolo')
                        else:
                            raise ValueError(f'Unknown annotation type {annotation_type}')
                        cas.add(glossa)

                    last_label = 'O'
                    last_end = -1
                    annotation_start = -1
                    annotation_type = None
            cas.to_xmi(target_dir / file_source.name.replace('.txt.bioes', '.xmi'), pretty_print=True)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python script_name.py <source_dir> <target_dir>")
        sys.exit(1)

    source_dir = sys.argv[1]
    target_dir = sys.argv[2]
    main(source_dir, target_dir)
