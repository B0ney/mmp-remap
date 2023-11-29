Simple CLI tool to re-map paths in lmms projects


# Requirements
* Python

# Recommended
* LMMS installed and configured.


# Resources that can be remapped:
* Audio - ``wav``, ``ogg``, ``mp3``, ``flac``, ``aiff``, ``ds``, ``spx``, ``voc``, ``aif``, ``au``
    - AudioFileProcessor
    - Sample Clip
    - SlicerT

* Soundfonts - ``.sf2``, ``.sf3``
    - SF2  Player

* VSTs - ``.dll``, ``.exe``, ``.so``
    - Vestige

# How to Use
```shell
python mmpap.py ./project.mmpz
```

There are 3 ways resources can be remapped:
* With an Index
* Multiple with matches
* Multiple with fancy regex

### Remap with an Index
The simplest method if you don't want to remap that many resources.

```shell

```

### Match based remapping

```shell

```

### Regex based remapping

```shell

```

## CLI args


# Compatibility
Should work across nearly all lmms versions
