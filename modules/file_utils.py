import os
import shutil
import tempfile
import json
from zipfile import ZipFile


def get_annots_file(path):
    with ZipFile(path) as myzip:
        with myzip.open("annotations.json") as json_file:
            return json.load(json_file)


def remove_from_zip(zipfname, *filenames):
    tempdir = tempfile.mkdtemp()
    try:
        tempname = os.path.join(tempdir, "new.zip")
        with ZipFile(zipfname, "r") as zipread:
            with ZipFile(tempname, "w") as zipwrite:
                for item in zipread.infolist():
                    if item.filename not in filenames:
                        data = zipread.read(item.filename)
                        zipwrite.writestr(item, data)
        shutil.move(tempname, zipfname)
    finally:
        shutil.rmtree(tempdir)


def save_zip(input_path, output_path, annots):
    # create output folder if it doesn't exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # copy the original file to output folder
    shutil.copy(input_path, os.path.join(output_path, input_path.split("/")[-1]))

    remove_from_zip(
        os.path.join(output_path, input_path.split("/")[-1]), "annotations.json"
    )
    with ZipFile(os.path.join(output_path, input_path.split("/")[-1]), "a") as newzip:
        newzip.writestr("annotations.json", json.dumps(annots))
