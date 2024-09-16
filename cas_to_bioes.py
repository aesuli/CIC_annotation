import io
import sys
import zipfile
from enum import Enum
from pathlib import Path

import cassis


class AnnotationState(str, Enum):
    any = 'any'
    annotated = 'annotated'
    unannotated = 'unannotated'


def read_cas_to_bioes(zip_file_path, username, annotation_state: AnnotationState = None, no_bioes_prefix=False):
    if annotation_state not in set(AnnotationState):
        raise ValueError(f'Must specifiy and annotation_state in {set(AnnotationState)}')


    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        inner_zip_files = [file_name for file_name in zip_ref.namelist() if file_name.endswith('INITIAL_CAS.zip')]
        for inner_zip_name in inner_zip_files:
            if inner_zip_name.replace('INITIAL_CAS',username) in zip_ref.namelist():
                inner_zip_name = inner_zip_name.replace('INITIAL_CAS',username)
            with zip_ref.open(inner_zip_name) as inner_zip_file:
                with zipfile.ZipFile(io.BytesIO(inner_zip_file.read())) as inner_zip_ref:
                    inner_file_list = inner_zip_ref.namelist()
                    with inner_zip_ref.open('TypeSystem.xml', mode='r') as typesystem_file:
                        typesystem = cassis.load_typesystem(typesystem_file)
                    token_type = typesystem.get_type('de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token')
                    sentence_type = typesystem.get_type(
                        'de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence')
                    glossa_type = typesystem.get_type('webanno.custom.Glossa')

                    annotations = []
                    annotated = 0
                    for file_name in inner_file_list:
                        if file_name.endswith('.xmi'):
                            with inner_zip_ref.open(file_name, mode='r') as xmi_file:
                                cas = cassis.load_cas_from_xmi(xmi_file, typesystem)
                                text = cas.sofa_string

                                for sentence in cas.select(sentence_type):
                                    sentence_annotations = []
                                    sentence_tokens = cas.select_covered(token_type, sentence)

                                    prev_label = 'O'
                                    for token in sentence_tokens:
                                        ner_label = 'O'

                                        for ne in cas.select_covering(glossa_type, token):
                                            if no_bioes_prefix:
                                                ner_label = 'AN'
                                            else:
                                                if prev_label == 'O':
                                                    ner_label = 'SOURCE|B-AN'
                                                else:
                                                    ner_label = 'SOURCE|I-AN'
                                            annotated += 1
                                            break
                                        prev_label = ner_label

                                        if not no_bioes_prefix and ner_label == 'O' and len(
                                                sentence_annotations) > 0 and len(sentence_annotations[-1]) > 0:
                                            if sentence_annotations[-1][3] == 'I-AN':
                                                sentence_annotations[-1] = (sentence_annotations[-1][0], token.begin, token.end, 'SOURCE|E-AN')
                                            elif sentence_annotations[-1][3] == 'B-AN':
                                                sentence_annotations[-1] = (sentence_annotations[-1][0], token.begin, token.end, 'SOURCE|S-AN')

                                        conll_line = (token.get_covered_text(), token.begin, token.end, ner_label)
                                        sentence_annotations.append(conll_line)

                                    annotations.append(sentence_annotations)

                    if (
                            annotation_state == AnnotationState.annotated and annotated > 0) or annotation_state == AnnotationState.any:
                        yield inner_zip_name, text, annotations
                    elif (
                            annotation_state == AnnotationState.unannotated and annotated == 0) or annotation_state == AnnotationState.any:
                        yield inner_zip_name, text, annotations


def main(zip_file_path, username):
    output_dir = Path('annotations_bioes')
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename, text, annotations in read_cas_to_bioes(zip_file_path, username, AnnotationState.any):
        with (output_dir / filename[filename.find('/') + 1:filename.rfind('/')]).open(mode='wt',
                  encoding='utf-8') as output_file:
            print(text.replace('\r',''),file=output_file, end='')
        with (output_dir / (filename[filename.find('/') + 1:filename.rfind('/')]+'.bioes')).open(mode='wt',
                                                                                      encoding='utf-8') as output_file:
            print(filename, len(annotations))
            for sentence in annotations:
                for token, begin, end, label in sentence:
                    print(f'{token} {begin} {end} {label}', file=output_file)
                print(file=output_file)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python script_name.py <zip_file_path> <username>")
        sys.exit(1)

    zip_file_path = sys.argv[1]
    username = sys.argv[2]
    main(zip_file_path, username)
