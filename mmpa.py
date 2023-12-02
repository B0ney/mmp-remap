#!/usr/bin/env python3

# Copyright (c) 2023 B0ney
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import argparse as arg
import re
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
SRC_XPATH = (".//*[@src]", "src")
VESTIGE_XPATH = (".//vestige", "plugin")

XPATH_ATTRS = [SRC_XPATH, VESTIGE_XPATH]


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


def write_mmp(xml: ET.ElementTree, path: str):
    """Output mmp xml data to a file.
    Will compress if the file extension is .mmpz
    """

    extension = get_file_ext(path)

    if extension == "mmpz":
        with open(path, "wb") as file:
            data = ET.tostring(xml.getroot())
            size = int.to_bytes(len(data), 4, byteorder="big")

            file.write(size)
            file.write(zlib.compress(data))
    else:
        xml.write(path, encoding="UTF-8")


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
    def get_lmmsrc_paths(path) -> Optional[Dict[str, str]]:
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
    def shorten_path(self, path: str) -> str:
        for alias, expanded in self.aliases().items():
            if path.startswith(str(expanded)):
                return path.replace(str(expanded), alias, 1)

        return path

    # TODO
    def path_in_lmmsrc(self, path: str) -> bool:
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
        print("ERROR: Could not find allowed extension for ", old_resource)
        return False

    extension = get_file_ext(new_resource)

    if extension not in allowed_extensions:
        print(f"ERROR: Resource can not be a '{extension}'")
        return False

    return True


class Remapper:
    """Remaps resources in LMMS projects"""

    __dataset: Dict[str, List[Instrument]]

    def __init__(self, mmp: ET.ElementTree):
        self.__dataset = {}

        for xpath, attrib in XPATH_ATTRS:
            for elem in mmp.iterfind(xpath):
                self.append_or_update(Instrument(attrib, elem))

    def get_resources(self) -> List[str]:
        """Returns a list of all the re-mappable resources"""

        return list(self.__dataset.keys())

    def get_resource(self, index: int) -> str:
        """Provides a resource given an index"""

        return self.get_resources()[index]

    def append_or_update(self, instr: Instrument):
        resource = instr.get_resource()

        # Do not add instruments with empty paths, because
        # we may give instruments the wrong file type
        if resource == "":
            return

        if self.__dataset.get(resource) is None:
            self.__dataset[resource] = [instr]
        else:
            self.__dataset[resource].append(instr)

    def list_mappings(self):
        """List all of the resources and its associated instruments"""

        for index, (resource, instruments) in enumerate(self.__dataset.items()):
            print(f"[{index}]", resource)

            plural = ""
            if len(instruments) > 1:
                plural = "S"
            print(f"        {len(instruments)} - REFERENCE{plural}\n")


    def remap_resource(self, resource: str, new_resource: str):
        """Remaps a given resource in the dataset"""

        if not extension_is_allowed(resource, new_resource):
            return

        instruments = self.__dataset.get(resource)

        if instruments is None:
            print(f"ERROR: key '{resource}' not found")
            return

        for instrument in instruments:
            instrument.update_resource(new_resource)

        # Use updated resource as the new key.
        self.__dataset[new_resource] = self.__dataset.pop(resource)


def remap_index(remapper: Remapper, index: int, new_resource: str):
    """Remaps a single resource from a given index"""

    resource = remapper.get_resource(index)
    remapper.remap_resource(resource, new_resource)


def remap_match(remapper: Remapper, to_match: str, replace: str):
    """Finds and replaces all matching strings for all resources"""

    for resource in remapper.get_resources():
        if to_match in resource:
            new_resource = resource.replace(to_match, replace)
            remapper.remap_resource(resource, new_resource)


def remap_regex(remapper: Remapper, pattern: str, replace: str):
    """Use regex to replace a pattern for all resources"""

    for resource in remapper.get_resources():
        new_resource = re.sub(pattern, replace, resource)

        if new_resource != resource:
            remapper.remap_resource(resource, new_resource)


# TODO
def alias_resources(remapper: Remapper, lmmsrc: LMMSRC):
    """Replace absolute paths for all resources with aliases specified by lmmsrc"""

    for resource in remapper.get_resources():
        aliased_res = lmmsrc.shorten_path(resource)

        if aliased_res != resource:
            remapper.remap_resource(resource, aliased_res)


def get_file_ext(path: str) -> str:
    return Path(path).suffix.strip(".").lower()


def validate_cli(cli: arg.Namespace) -> arg.Namespace:
    if not cli.path.exists():
        print(f"ERROR: path '{cli.path}' file does not exist")
        sys.exit(1)

    if cli.config is not None:
        if not Path(cli.config).exists():
            print("ERROR: lmmsrc path override does not exist")
            sys.exit(1)

    return cli


def build_cli() -> arg.Namespace:
    parser = arg.ArgumentParser()

    parser.add_argument("path", type=Path, help="Path to LMMS project file")
    parser.add_argument("-c", "--config", help="Override default lmmsrc path file")
    # parser.add_argument(
    #     "-p",
    #     "--preserve",
    #     help="Preserve file metadata in mmp",
    #     action="store_true"
    # )
    # parser.add_argument(
    #     "-a",
    #     "--auto",
    #     help="Automatically alias absolute paths if they can be located with lmmsrc",
    #     action="store_true",
    #     default=False,
    # )

    subparsers = parser.add_subparsers(
        title="subcommands",
        description="For when you need to do something quick",
        help="additional help",
        required=False,
        dest="mode",
    )

    # create parser for the "match" subcommand
    parser_match = subparsers.add_parser(
        "match", help="Re-map project resources with string matching"
    )
    parser_match.add_argument("match", type=str)
    parser_match.add_argument("replace", type=str)
    parser_match.add_argument(
        "-o", "--out", help="Specify the output file", required=True
    )

    # create parser for the re command
    parser_re = subparsers.add_parser(
        "re", help="Re-map project resources with regular expressions"
    )
    parser_re.add_argument("pattern", type=str)
    parser_re.add_argument("replace", type=str)
    parser_re.add_argument("-o", "--out", help="Specify the output file", required=True)

    # subcommand to list resources
    parser_list = subparsers.add_parser(
        "list",
        help="List all of the resources and its associated instruments",
    )

    return validate_cli(parser.parse_args())


def main():
    cli = build_cli()
    # config = LMMSRC.default_path()

    # if cli.config is not None:
    #     print("INFO: Using user-provided lmmsrc override")
    #     config = Path(cli.config)

    # if not config.exists():
    #     print("ERROR: Could not find .lmmsrc.xml in your user directory")
    #     sys.exit(1)

    # TODO
    # lmmsrc = LMMSRC(config)

    mmp = read_xml(cli.path)

    remapper = Remapper(mmp)

    # if cli.auto:
    #     alias_resources(remapper, lmmsrc)

    if cli.mode == "list":
        print("INFO: Listing all resources and its references\n")
        remapper.list_mappings()

        sys.exit(0)

    if cli.mode == "match":
        remap_match(remapper, cli.match, cli.replace)
        write_mmp(mmp, cli.out)

        sys.exit(0)

    if cli.mode == "re":
        remap_regex(remapper, cli.pattern, cli.replace)
        write_mmp(mmp, cli.out)

        sys.exit(0)

    # TODO: implement other interface
    print("nothing to do...")


if __name__ == "__main__":
    main()
