#!/usr/bin/env python

import xml.etree.ElementTree as ET
import zlib

from typing import Dict, List, Optional
from pathlib import Path



# XPATH syntax to select all xml elements that have the "src" attribute.
SRC_XPATH = ".//*[@src]"


# Allowed extensions
AUDIO_EXT = ["wav", "ogg", "flac", "aiff"]
SOUNDFONT_EXT = ["sf2", "sf3"]



USER_PROJECTS = "userprojects"
USER_SAMPLE = "usersample"
USER_SOUNDFONT = "usersoundfont"



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



mmp = read_xml("./cyberpunk-18.mmp")

dataset: Dict[str, List[ET.Element]] = {}


def append_to_or_update(key: str, value: ET.Element, dict: Dict[str, List[ET.Element]]):
    if dict.get(key) is None:
        dict[key] = [value]
    else:
        dict[key].append(value)


for i, e in enumerate(mmp.iterfind(SRC_XPATH)):
    append_to_or_update(e.attrib["src"], e, dataset)


for k, v in dataset.items():
    print(k, "\n    - references:", len(v), "\n")

# replace attribute
# for e in dataset["usersample:test.flac"]:
#     e.attrib["src"] = "usersample:test2.flac"


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