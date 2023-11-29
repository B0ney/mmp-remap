#!/usr/bin/env python

import argparse as arg
import sys
import xml.etree.ElementTree as ET
import zlib

from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path


# Allowed extensions
AUDIO_EXT = ["wav", "ogg", "mp3", "flac", "aiff", "ds", "spx", "voc", "aif", "au"]
SOUNDFONT_EXT = ["sf2", "sf3"]
VST_EXT = ["dll", "exe", ".so"]

# Aliases used in LMMS projects
USER_PROJECTS = "userprojects"
USER_SAMPLE = "usersample"
USER_SOUNDFONT = "usersoundfont"
USER_VST = "uservst"


# XPATH syntax to select all xml elements that have the "src" attribute.
SRC_XPATH = ".//*[@src]"
VESTIGE_XPATH = ".//vestige"

XPATH_ATTRS = [(SRC_XPATH, "src"), (VESTIGE_XPATH, "plugin")]


def read_xml(path: str) -> ET.ElementTree:
    """Read xml data from a generic LMMS datafile
    into an editable xml tree
    """

    with open(path, "rb") as file:
        try:
            file.seek(4)  # skip size field
            xml_data = ET.fromstring(zlib.decompress(file.read()))
            return ET.ElementTree(xml_data)

        except zlib.error:
            return ET.parse(path)


# TODO: what if the user doesn't have an lmmsrc file?
class LMMSRC:
    """Uses your ``.lmmsrc.xml`` file to validate and shorten resources added by the user.

    Resources in lmms project files should not point to absolute paths.

    Keeping resources only accessible by lmmsrc makes them more portable.
    """

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
    def default_path() -> Path:
        """Get file location of ``.lmmsrc.xml`` in user directory"""

        return Path.home().joinpath(".lmmsrc.xml")

    @staticmethod
    def get_lmmsrc_paths(path: Path | str) -> Optional[Dict[str, str]]:
        """Get attributes from "Paths" tag in ``lmmsrc`` as a dictionary"""

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
        """Expand shorthand paths used in LMMS project files.

        E.g. ``usersample:brownnoise.ogg`` -> ``C:\\Users\\yourname\\LMMS\\samples\\brownnoise.ogg``
        """

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
        for alias, expanded in self.aliases().items():
            if path.startswith(str(expanded)):
                return path.replace(str(expanded), alias, 1)

        return path

    # TODO
    def is_path_in_lmmsrc(self, path: str) -> bool:
        path = self.expand_alias(path)

        # return Path(path).resolve() in [lmmsrc.sf2_dir.parents]
        return False


@dataclass
class Instrument:
    """An LMMS instrument with an external resource.

    Updating a resource will also update the xml tree it is referencing.
    """

    attrib: str
    elem: ET.Element

    def update_resource(self, value: str):
        self.elem.attrib[self.attrib] = value

    def get_resource(self) -> str:
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


def extension_is_allowed(
    old_resource: str,
    new_resource: str,
) -> bool:
    """Check if the new resource has a valid extension.

    Done to prevent remapping instruments with the wrong file type.

    E.g ``usersample:kick.wav`` to ``uservst:vital.dll``
    """

    allowed_extensions = get_allowed_extensions(get_file_ext(old_resource))

    if allowed_extensions is None:
        print("ERROR: Could not find allowed extension")
        return False

    extension = get_file_ext(new_resource)

    if extension not in allowed_extensions:
        print(f"ERROR: Resource can not be a '{extension}'")
        return False

    return True


class Remapper:
    """Remaps resources in LMMS projects"""

    dataset: Dict[str, List[Instrument]]

    def __init__(self) -> None:
        self.dataset = {}

    def build_mapping(self, mmp: ET.ElementTree):
        for xpath, attrib in XPATH_ATTRS:
            for elem in mmp.iterfind(xpath):
                self.append_or_update(Instrument(attrib, elem))

    def append_or_update(self, instr: Instrument):
        resource = instr.get_resource()

        # Do not add instruments with empty paths, because
        # we may give instruments the wrong file type
        if resource == "":
            return

        if self.dataset.get(resource) is None:
            self.dataset[resource] = [instr]
        else:
            self.dataset[resource].append(instr)

    def list_mappings(self):
        """List all of the resources and its associated instruments"""

        for index, (resource, instruments) in enumerate(self.dataset.items()):
            print(f"[{index}]", resource)

            for instrument in instruments:
                print(f"        * {instrument.name()}")
            print()

    def remap_resource(self, resource: str, new_resource: str):
        """Remaps a given resource in the dataset"""

        if not extension_is_allowed(resource, new_resource):
            return

        instruments = self.dataset.get(resource)

        if instruments is None:
            print(f"key '{resource}' not found")
            return

        for instrument in instruments:
            instrument.update_resource(new_resource)


def get_file_ext(path: str) -> str:
    return Path(path).suffix.strip(".")


def validate_cli(cli: arg.Namespace):
    if cli.c is not None:
        if not Path(cli.c).exists():
            print("ERROR: lmmsrc path override does not exist")
            sys.exit(1)

    pass


def main(argv: List[str]):
    # parser = arg.ArgumentParser()

    # parser.add_argument("-c",
    #     default=None,
    #     help="Override default lmmsrc path file"
    # )

    # cli = parser.parse_args()

    # validate_cli(cli)

    config = LMMSRC.default_path()

    # if cli.c is not None:
    #     config = Path(cli.c)

    if not config.exists():
        print("ERROR: could not find .lmmsrc.xml in your user directory")
        sys.exit(1)

    lmmsrc = LMMSRC(config)

    mmp = read_xml("./test/80's.mmpz")

    remapper = Remapper()

    remapper.build_mapping(mmp)

    remapper.list_mappings()

    # test
    remapper.remap_resource("drumsynth/effects/Cicada.ds", "kick.wav")

    print("Writing out lmms file...")
    mmp.write("test.mmp")


if __name__ == "__main__":
    main(sys.argv[1:])
