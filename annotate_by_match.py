import io
import os.path
import sys
import zipfile

import cassis


def main(zip_file_path, username,overwrite=False):
    annotations = read_annotations(zip_file_path,username,overwrite)
    annotate(zip_file_path, username, annotations)

def read_annotations(zip_file_path, username, overwrite=False):
    if overwrite or not os.path.exists('annotations.txt'):
        suffix = username + ".zip"

        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            inner_zip_files = [file_name for file_name in zip_ref.namelist() if file_name.endswith(suffix)]

            annotations = list()
            for inner_zip_name in inner_zip_files:
                with zip_ref.open(inner_zip_name) as inner_zip_file:
                    with zipfile.ZipFile(io.BytesIO(inner_zip_file.read())) as inner_zip_ref:
                        inner_file_list = inner_zip_ref.namelist()
                        with inner_zip_ref.open('TypeSystem.xml', mode='r') as typesystem_file:
                            typesystem = cassis.load_typesystem(typesystem_file)
                        for file_name in inner_file_list:
                            if file_name.endswith('.xmi'):
                                with inner_zip_ref.open(file_name, mode='r') as xmi_file:
                                    cas = cassis.load_cas_from_xmi(xmi_file, typesystem)
                                    annos = cas.select_all()
                                    annotated = 0
                                    for anno in annos:
                                        if anno.type.name.find('custom') > 0:
                                            annotations.append(f'{anno.get_covered_text()}')
                                            annotated += 1
                                    if annotated > 0:
                                        print(inner_zip_name, annotated, len(annotations), len(set(annotations)))
            annotations = set(annotations)

            with open('annotations.txt',mode='wt',encoding='utf-8') as output_file:
                for annotation in sorted(annotations):
                    print(annotation,file=output_file)
            return annotations

    with open('annotations.txt', mode='rt', encoding='utf-8') as input_file:
        return set([line.strip() for line in input_file.readlines()])

def annotate(zip_file_path, username, annotations):
    suffix = username + ".zip"

    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        inner_zip_files = [file_name for file_name in zip_ref.namelist() if file_name.endswith(suffix)]
        for inner_zip_name in inner_zip_files:
            with zip_ref.open(inner_zip_name) as inner_zip_file:
                with zipfile.ZipFile(io.BytesIO(inner_zip_file.read())) as inner_zip_ref:
                    inner_file_list = inner_zip_ref.namelist()
                    with inner_zip_ref.open('TypeSystem.xml', mode='r') as typesystem_file:
                        typesystem = cassis.load_typesystem(typesystem_file)
                    for file_name in inner_file_list:
                        if file_name.endswith('.xmi'):
                            with inner_zip_ref.open(file_name, mode='r') as xmi_file:
                                cas = cassis.load_cas_from_xmi(xmi_file, typesystem)
                                annos = cas.select_all()
                                annotated = 0
                                for anno in annos:
                                    if anno.type.name.find('custom') > 0:
                                        annotated += 1
                                        break
                                if annotated == 0:
                                    text = cas.get_document_annotation().get_covered_text()
                                    for annotation in annotations:
                                        if annotation in text:
                                            annotated += 1
                                print(inner_zip_name, annotated)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python script_name.py <zip_file_path> <username>")
        sys.exit(1)

    zip_file_path = sys.argv[1]
    username = sys.argv[2]
    main(zip_file_path, username)
