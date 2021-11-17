import upserverlib
import json
from shutil import copyfile

Support = upserverlib.Support


class SdeskInputFile(upserverlib.InputFile):
    """ " Input class with methods to interact with Sdesk data manager"""

    def __init__(self, data, process):
        super().__init__(data)
        self.process = process
        self.subject = None
        file_subject = self.properties.get("subject", None)
        if file_subject:
            self.subject = SdeskInputSubject(file_subject, self.process)

    def save_custom_properties(self):
        output = self.process.get_or_create_output_file_update(self)
        output.custom_properties.update(self.custom_properties)


class SdeskInputSubject(upserverlib.InputSubject):
    """ " Input class with methods to interact with Sdesk data manager"""

    def __init__(self, data, process):
        super().__init__(data)
        self.process = process

    def save_custom_properties(self):
        output = self.process.get_or_create_output_subject_update(
            self, fields=["custom_properties"]
        )
        output.custom_properties.update(self.custom_properties)

    def save_as_aggregated_data(self, input_path, name="aggregated_data"):
        output = self.process.get_or_create_output_subject_update(
            self, fields=["aggregated_data"]
        )
        copyfile(input_path, output.aggregated_data.path)


class InputItems:
    def __init__(self, data_class, process=None):
        self._data_class = data_class
        self._file_items = []
        self.process = process

    def add_item(self, data):
        _type = data["type"]
        self._file_items.append(self._data_class(data, self.process))

    def __getitem__(self, index):
        return self._file_items[index]


class Process(upserverlib.Process):
    def _get_input_files(self):
        i = InputItems(process=self, data_class=SdeskInputFile)

        with open(upserverlib.INPUT_FILESYSTEM) as fp:
            rv = json.load(fp)
            for x in rv.get("input", []):
                if x["type"] == "file":
                    i.add_item(x)
            return i

    def _get_input_subjects(self):
        i = InputItems(process=self, data_class=SdeskInputSubject)

        with open(upserverlib.INPUT_FILESYSTEM) as fp:
            rv = json.load(fp)
            for x in rv.get("input", []):
                if x["type"] == "subject":
                    i.add_item(x)
            return i


def json_to_text(json_data):
    text = "HEADER\n"
    for key in json_data:
        text += "{0}: {1}\n".format(key, json_data[key])
    text += "\n"
    return text


def force_str(object):
    try:
        return str(object)
    except:
        pass
    try:
        return object.encode("utf-8")
    except:
        pass
    try:
        return object.encode("utf-8", "ignore").decode("utf-8")
    except:
        pass
    try:
        return object.encode("ascii", "ignore").decode("ascii")
    except:
        return ""


def write_tsv_file(file_path, columns, data, pre_header=""):
    """Create tab separated value file from data rows."""
    with open(file_path, "w") as fp:
        fileposition = 0
        if pre_header:
            lines = pre_header.split("\n")
            pre_header = "\n".join(["# " + line for line in lines]) + "\n\n"
            fp.write(pre_header)
            fileposition += len(pre_header)

        # Header
        column_names = ["[{0}]".format(col.replace("\n", " ")) for col in columns]
        column_line = "\t".join(column_names) + "\n"
        fp.write(column_line)
        fileposition += len(column_line)
        # Data
        for row in data:
            strings = [force_str(elem) for elem in row]
            data_line = "\t".join(strings) + "\n"
            fp.write(data_line)
            fileposition += len(data_line)

    return fileposition
