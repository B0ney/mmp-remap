#!/usr/bin/env python

from dataclasses import dataclass
import xml.etree.ElementTree as ET
import zlib

from typing import Dict, List, Optional
from pathlib import Path


# XPATH syntax to select all xml elements that have the "src" attribute.
SRC_XPATH = ".//*[@src]"
VESTIGE_XPATH = "//vestige"


# Allowed extensions
AUDIO_EXT = ["wav", "ogg", "flac", "aiff", "ds", "spx", "voc", "aif", "au"]
SOUNDFONT_EXT = ["sf2", "sf3"]
VST_EXT = ["dll", "exe"]


USER_PROJECTS = "userprojects"
USER_SAMPLE = "usersample"
USER_SOUNDFONT = "usersoundfont"
USER_VST = "uservst"


def read_xml(path: str) -> ET.ElementTree:
    ''' Read xml data from a generic LMMS datafile 
        into an editable xml tree 
    '''

    with open(path, "rb") as file:
        try:
            file.seek(4) # skip size field
            xml_data = ET.fromstring(zlib.decompress(file.read()))
            return ET.ElementTree(xml_data)

        except zlib.error:
            return ET.parse(path)


def lmmsrc_path() -> Path:
    ''' Get file location of ```.lmmsrc.xml``` in user directory '''

    return Path.home().joinpath(".lmmsrc.xml")


# TODO: what if the user doesn't have an lmmsrc
def get_lmmsrc_paths(path: Path | str) -> Optional[Dict[str, str]]:
    ''' Get attributes from "Paths" tag in ```lmmsrc``` as a dictionary '''

    with open(path, "rb") as file:
        tree_root: Optional[ET.Element] = ET.parse(file).getroot()
        
        if tree_root is None:
            return None
        
        paths: Optional[ET.Element] = tree_root.find("paths")

        if paths is None:
            return None
        
        return paths.attrib


@dataclass
class Mapper:
    attrib: str
    elem: ET.Element

    def update(self, value: str):
        self.elem.attrib[self.attrib] = value

    def get(self) -> str:
        return self.elem.attrib[self.attrib]
    
    def name(self) -> str:
        return self.elem.tag


mmp = read_xml("./slicerT.mmpz")

dataset: Dict[str, List[Mapper]] = {}


def append_to_or_update(value: Mapper, dict: Dict[str, List[Mapper]]):
    key = value.get()
    if dict.get(key) is None:
        dict[key] = [value]
    else:
        dict[key].append(value)

    
def remap(key: str, new_value: str, dataset: Dict[str, List[Mapper]]):
    mappers = dataset.get(key)

    if mappers is None:
        print(f"key '{key}' not found")
        return
    
    for elem in mappers:
        elem.update(new_value)


def allowed_extensions(ext: str) -> Optional[List[str]]:
    filters = [
        AUDIO_EXT,
        SOUNDFONT_EXT,
        VST_EXT,
    ]

    for filter in filters:
        if ext in filter:
            return filter

    return None


for e in mmp.iterfind(SRC_XPATH):
    append_to_or_update(Mapper("src", e), dataset)


for e in mmp.iterfind(VESTIGE_XPATH):
    append_to_or_update(Mapper("plugin", e), dataset)


for k, v in dataset.items():
    print(k, )
    for elem in v:
        print(f"        * {elem.name()}")
    print()


# replace attribute
# for e in dataset["userprojects:cyberpunk/resources/Loop funk-7.wav"]:
#     e.update("usersample:test2.flac")

# write xml back to file
mmp.write("test.mmp")


# list out paths in lmmsrc
print(lmmsrc_path())
a = get_lmmsrc_paths(lmmsrc_path())

if a is not None:
    for k,v in a.items():
        print(k, v) 


def main():
    pass


if __name__ == "__main__":
    pass