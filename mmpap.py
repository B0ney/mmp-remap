#!/usr/bin/env python

import argparse as arg
import sys
import xml.etree.ElementTree as ET
import zlib

from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path


# Allowed extensions
AUDIO_EXT = ["wav", "ogg", "flac", "aiff", "ds", "spx", "voc", "aif", "au"]
SOUNDFONT_EXT = ["sf2", "sf3"]
VST_EXT = ["dll", "exe"]

# Aliases used in LMMS projects
USER_PROJECTS = "userprojects"
USER_SAMPLE = "usersample"
USER_SOUNDFONT = "usersoundfont"
USER_VST = "uservst"


# XPATH syntax to select all xml elements that have the "src" attribute.
SRC_XPATH = ".//*[@src]"
VESTIGE_XPATH = ".//vestige"


XPATH_ATTRS = [
    (SRC_XPATH, "src"),
    (VESTIGE_XPATH, "plugin")
]


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
    ''' Get file location of ``.lmmsrc.xml`` in user directory '''

    return Path.home().joinpath(".lmmsrc.xml")


# TODO: what if the user doesn't have an lmmsrc file
class LMMSRC:
    def __init__(self, path: Path):
        paths = self.get_lmmsrc_paths(path)

        if paths is None:
            raise EnvironmentError
        
        self.sf2_dir = Path(paths["sf2dir"])
        self.vst_dir = Path(paths["vstdir"])

        self.working_dir = Path(paths["workingdir"])
        self.samples_dir = self.working_dir.joinpath("samples")
        self.projects_dir = self.working_dir.joinpath("projects")

    @staticmethod
    def get_lmmsrc_paths(path: Path | str) -> Optional[Dict[str, str]]:
        ''' Get attributes from "Paths" tag in ``lmmsrc`` as a dictionary '''

        with open(path, "rb") as file:
            tree_root: Optional[ET.Element] = ET.parse(file).getroot()
            
            if tree_root is None:
                return None
            
            paths: Optional[ET.Element] = tree_root.find("paths")

            if paths is None:
                return None
            
            return paths.attrib
    

    def aliases(self) -> Dict[str, Path]:
        aliases = {
            USER_PROJECTS: self.projects_dir,
            USER_SAMPLE: self.samples_dir,
            USER_SOUNDFONT: self.sf2_dir,
            USER_VST: self.vst_dir,
        }
        
        return aliases
    
    def expand_alias(self, path: str) -> str:
        ''' Expand shorthand paths used in lmms project files.

            E.g. ``usersample:brownnoise.ogg`` -> ``C:\\Users\\yourname\\LMMS\\samples\\brownnoise.ogg`` 
        '''

        split_path = path.split(":", 1)

        if len(split_path) < 2:
            return path
        
        alias = split_path[0]
        resource = split_path[1]

        expanded = self.aliases().get(alias)

        if expanded is None:
            print(f"Unknown alias '{alias}'")
            return path
        
        return str(expanded.joinpath(resource))
    
    
    # TODO
    def shorten(self, path: str) -> str:
        for (alias, expanded) in self.aliases().items():
            if path.startswith(str(expanded)):
                return path.replace(str(expanded), alias, 1)
        
        return path
                

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


def get_allowed_extensions(ext: str) -> Optional[List[str]]:
    filters = [
        AUDIO_EXT,
        SOUNDFONT_EXT,
        VST_EXT,
    ]

    for filter in filters:
        if ext in filter:
            return filter

    return None


def append_to_or_update(value: Mapper, dict: Dict[str, List[Mapper]]):
    key = value.get()
    
    if key == "":
        key = "EMPTY"

    if dict.get(key) is None:
        dict[key] = [value]
    else:
        dict[key].append(value)

    
def remap(key: str, new_value: str, dataset: Dict[str, List[Mapper]]):
    ''' Remaps a given resource in the dataset '''

    allowed_extensions = get_allowed_extensions(get_ext(key))

    if allowed_extensions is None:
        print("Could not find allowed extension")
        return
    
    extension = get_ext(new_value)
    
    if extension not in allowed_extensions:
        print(f"resource can not be a '{extension}'")
        return

    mappers = dataset.get(key)

    if mappers is None:
        print(f"key '{key}' not found")
        return
    
    for elem in mappers:
        elem.update(new_value)


def get_ext(path: str) -> str:
    return Path(path).suffix.strip('.')

def estimate_new_path(path: str, lmmsrc: LMMSRC):
    pass


def is_path_in_lmmsrc(lmmsrc: LMMSRC, path: str) -> bool:
    path = lmmsrc.expand_alias(path)
    
    # return Path(path).resolve() in [lmmsrc.sf2_dir.parents]
    return False


mmp = read_xml("./test/80's.mmpz")

dataset: Dict[str, List[Mapper]] = {}


# build mapping
for (xpath, attrib) in XPATH_ATTRS:
    for elem in mmp.iterfind(xpath):
        append_to_or_update(Mapper(attrib, elem), dataset)



for i, (k, v) in enumerate(dataset.items()):
    print(f"[{i}]", k)
    for elem in v:
        print(f"        * {elem.name()}")
    print()


remap("uiui", "arg.wav", dataset)

# write xml back to file
mmp.write("test.mmp")

lmmsrc = LMMSRC(lmmsrc_path())

print(lmmsrc.projects_dir)
print(lmmsrc.samples_dir)

print(lmmsrc.expand_alias("usersoundfont:FluidR3_GM.sf2"))




def validate_cli(cli: arg.Namespace):
    if cli.c is not None:
        if not Path(cli.c).exists():
            print("ERROR: lmmsrc path override does not exist")
            sys.exit(1)
    
    pass

def main():
    parser = arg.ArgumentParser()
    
    parser.add_argument("-c",
        default=None,
        help="Override default lmmsrc path file"
    )

    cli = parser.parse_args()

    validate_cli(cli)


    config = lmmsrc_path()

    if cli.c is not None:
        config = Path(cli.c)

    if not config.exists():
        print("ERROR: could not find .lmmsrc.xml in your user directory")
        sys.exit(1)
    

    lmmsrc = LMMSRC(config)
    

    pass


if __name__ == "__main__":
    main()