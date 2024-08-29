import io
import os.path
import sys
import zipfile
from enum import Enum

import cassis

class AnnotationState(str, Enum):
    any = 'any'
    annotated = 'annotated'
    unannotated = 'unannotated'

def read_cas_to_bioes(zip_file_path, username, annotation_state:AnnotationState = None):

    if annotation_state not in set(AnnotationState):
        raise ValueError(f'Must specifiy and annotation_state in {set(AnnotationState)}')

    suffix = username + ".zip"

    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        inner_zip_files = [file_name for file_name in zip_ref.namelist() if file_name.endswith(suffix)]

        for inner_zip_name in inner_zip_files:
            with zip_ref.open(inner_zip_name) as inner_zip_file:
                with zipfile.ZipFile(io.BytesIO(inner_zip_file.read())) as inner_zip_ref:
                    inner_file_list = inner_zip_ref.namelist()
                    with inner_zip_ref.open('TypeSystem.xml', mode='r') as typesystem_file:
                        typesystem = cassis.load_typesystem(typesystem_file)
                    token_type = typesystem.get_type('de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Token')
                    sentence_type = typesystem.get_type(
                        'de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence')
                    glossa_type = typesystem.get_type('webanno.custom.Glossa')

                    document_with_labels = []
                    annotated = 0
                    for file_name in inner_file_list:
                        if file_name.endswith('.xmi'):
                            with inner_zip_ref.open(file_name, mode='r') as xmi_file:
                                cas = cassis.load_cas_from_xmi(xmi_file, typesystem)

                                for sentence in cas.select(sentence_type):
                                    sentence_with_labels = []
                                    sentence_tokens = cas.select_covered(token_type, sentence)

                                    prev_label = 'O'
                                    for token in sentence_tokens:
                                        ner_label = 'O'

                                        for ne in cas.select_covering(glossa_type, token):
                                            if prev_label == 'O':
                                                ner_label = 'B-AN'
                                                prev_label = 'AN'
                                            else:
                                                ner_label = 'I-AN'
                                            annotated += 1
                                            break

                                        if ner_label == 'O' and len(sentence_with_labels) > 0 and len(sentence_with_labels[-1]) > 0:
                                            if sentence_with_labels[-1][1] == 'I-AN':
                                                sentence_with_labels[-1] = (sentence_with_labels[-1][0], 'E-AN')
                                            elif sentence_with_labels[-1][1] == 'B-AN':
                                                sentence_with_labels[-1] = (sentence_with_labels[-1][0], 'S-AN')

                                        conll_line = (token.get_covered_text(), ner_label)
                                        sentence_with_labels.append(conll_line)

                                    document_with_labels.append(sentence_with_labels)

                    if (annotation_state==AnnotationState.annotated and annotated > 0) or annotation_state==AnnotationState.any:
                        yield inner_zip_name, document_with_labels
                    elif (annotation_state==AnnotationState.unannotated and annotated == 0) or annotation_state==AnnotationState.any:
                        yield inner_zip_name, document_with_labels


def main(zip_file_path, username, overwrite=False):
    if overwrite or not os.path.exists('train_data.txt'):
        suffix = username + ".zip"

        with open('train_data.txt',mode='wt',encoding='utf-8') as output_file:
            for filename, annotations in read_cas_to_bioes(zip_file_path,username,AnnotationState.annotated):
                print(filename,len(annotations))
                for sentence in annotations:
                    for token,label in sentence:
                        print(f'{token} {label}',file=output_file)
                    print(file=output_file)

        with open('test_data.txt',mode='wt',encoding='utf-8') as output_file:
            for filename, annotations in read_cas_to_bioes(zip_file_path,username,AnnotationState.unannotated):
                print(filename,len(annotations))
                for sentence in annotations:
                    for token, label in sentence:
                        print(f'{token} {label}', file=output_file)
                    print(file=output_file)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python script_name.py <zip_file_path> <username>")
        sys.exit(1)

    zip_file_path = sys.argv[1]
    username = sys.argv[2]
    main(zip_file_path, username)
