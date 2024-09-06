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


def main(source_dir, target_dir):
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
            text = text.replace('\n','\r\n')
            cas.sofa_string =text
            cas.sofa_mime = 'text'
            last_label = 'O'
            last_end = -1
            annotation_start = -1
            for line in input_file:
                line = line.strip()
                if len(line) > 0:
                    token, start, end, label = line.split(' ')
                    if not label.endswith('AN') and last_label == 'AN':
                        glossa = GlossaAnnotation(begin=int(annotation_start), end=int(last_end), Tipo='Allegazione normativa')
                        cas.add(glossa)
                        last_end = -1
                        annotation_start = -1
                    elif label.endswith('AN') and last_label == 'O':
                        annotation_start = start

                    last_end = end

                    if label.endswith('AN'):
                        last_label = 'AN'
                    else:
                        last_label = 'O'
                else:
                    last_label = 'O'
                    last_end = -1
                    annotation_start = -1
            cas.to_xmi(target_dir / file_source.name.replace('.txt.bioes', '.xmi'), pretty_print=True)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python script_name.py <source_dir> <target_dir>")
        sys.exit(1)

    source_dir = sys.argv[1]
    target_dir = sys.argv[2]
    main(source_dir, target_dir)
