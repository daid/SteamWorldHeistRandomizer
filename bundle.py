import zipfile
import os
import zlib
import struct
import xml.etree.ElementTree as ET
import re
from typing import Optional


class XmlNode:
    def __init__(self, etree: ET.Element, parent: Optional[ET.Element]):
        self.__etree = etree
        self.__parent = parent

    @property
    def tag(self):
        return self.__etree.tag

    @property
    def text(self):
        return self.__etree.text

    @text.setter
    def text(self, value):
        self.__etree.text = value

    def __iter__(self):
        return iter([XmlNode(child, self.__etree) for child in self.__etree])

    def getByName(self, name):
        for e in self.__etree:
            if e.find("Name").text == name:
                return XmlNode(e, self.__etree)
        return None

    def __getitem__(self, key):
        e = self.__etree.find(key)
        if e is None:
            return None
        return e.text

    def __setitem__(self, key, value):
        e = self.__etree.find(key)
        if e is None:
            ET.SubElement(self.__etree, key).text = value
        else:
            e.text = value

    def __delitem__(self, key):
        e = self.__etree.find(key)
        if e is not None:
            self.__etree.remove(e)

    def subNode(self, tag, **kwargs) -> Optional["XmlNode"]:
        for e in self.__etree.findall(tag):
            skip = False
            for k, v in kwargs.items():
                if k not in e.attrib or e.attrib[k] != v:
                    skip = True
            if not skip:
                return XmlNode(e, self.__etree)
        return None

    def newChild(self, tag) -> "XmlNode":
        e = ET.SubElement(self.__etree, tag)
        return XmlNode(e, self.__etree)

    def attr(self, key, value=None) -> str:
        if value is None:
            return self.__etree.attrib.get(key)
        self.__etree.attrib[key] = value
        return value

    def delete(self):
        self.__parent.remove(self.__etree)

    def __repr__(self):
        return "%s:%s" % (self.__etree.tag, ["%s=%s" % (k, v) for k, v in self.__etree.attrib.items()])


class XmlRoot(XmlNode):
    def __init__(self, storage_path, data):
        self.__storage_path = storage_path
        self.__etree = ET.fromstring(data)
        super().__init__(self.__etree, None)

    def save(self):
        ET.indent(self.__etree)
        os.makedirs(os.path.dirname(self.__storage_path), exist_ok=True)
        open(self.__storage_path, "wb").write(ET.tostring(self.__etree))


class CSVFile:
    def __init__(self, storage_path):
        self.__storage_path = storage_path
        cdata = open(storage_path, "rb").read()
        self.__data = zlib.decompress(cdata[4:])
        assert struct.unpack("<I", cdata[:4])[0] == len(self.__data)
        if not os.path.exists(storage_path + ".backup"):
            open(storage_path + ".backup", "wb").write(cdata)

    def save(self) -> None:
        cdata = struct.pack("<I", len(self.__data)) + zlib.compress(self.__data, level=9)
        open(self.__storage_path, "wb").write(cdata)

    def set(self, key: str, value: str) -> None:
        key = key.encode("utf-8")
        value = value.encode("utf-8")
        parts = self.__data.split(b"\n")
        for idx, part in enumerate(parts):
            values = part.split(b"\t")
            if values[0] == key:
                values[1] = value
                part = b"\t".join(values)
                parts[idx] = part
                self.__data = b"\n".join(parts)
                return


class Bundle:
    def __init__(self, main_path):
        self.__main_path = main_path
        self.__xml_files = {}
        self.__csv_files = {}

    def load(self, bundle_name) -> bool:
        zipfilename = os.path.join(self.__main_path, bundle_name, "data01.impak")
        if not os.path.exists(zipfilename):
            return False
        z = zipfile.ZipFile(zipfilename, "r")
        for file in z.namelist():
            if file.endswith(".xml") or file.endswith(".ge"):
                data = z.read(file)
                # We need to fix some xml parsing issues.
                # First, strip out all comments, as those mess up the parser sometimes.
                while data.find(b'<!--') >= 0:
                    start = data.find(b'<!--')
                    next = data.find(b'<!--', start+4)
                    end = data.find(b'-->', start+4)
                    if end < 0:
                        break
                    if 0 <= next < end:
                        start = next
                    data = data[:start] + data[end+3:]
                # Next we need to remove the leading spaces
                data = data.strip()
                node = XmlRoot(os.path.join(self.__main_path, bundle_name, file), data)
                self.__xml_files[os.path.join(bundle_name, file)] = node
        return True

    def clean(self) -> None:
        # Clean up old extracted files.
        for filename in self.__xml_files.keys():
            if os.path.exists(os.path.join(self.__main_path, filename)):
                os.remove(os.path.join(self.__main_path, filename))
        for base_path, directories, files in os.walk(self.__main_path):
            for file in files:
                if file.endswith(".backup"):
                    filename = os.path.join(base_path, file[:-7])
                    os.unlink(filename)
                    os.rename(filename + ".backup", filename)

    def save(self) -> None:
        for item in self.__xml_files.values():
            item.save()
        for item in self.__csv_files.values():
            item.save()

    def getNodes(self, tag) -> XmlNode:
        for root in self.__xml_files.values():
            for child in root:
                if child.tag == tag:
                    yield child

    def getNode(self, tag, name) -> XmlNode:
        for root in self.__xml_files.values():
            for child in root:
                if child.tag == tag and child["Name"] == name:
                    return child
        return None

    def getCSV(self, filename) -> CSVFile:
        if filename not in self.__csv_files:
            self.__csv_files[filename] = CSVFile(os.path.join(self.__main_path, "Bundle", filename))
        return self.__csv_files[filename]
