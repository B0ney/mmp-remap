CLI tool to re-map paths in LMMS projects.

**Note**: This is not a path editor; you cannot edit individual instruments.

# Requirements
* Python

# Recommended
* LMMS installed and configured.


# Resources that can be re-mapped:
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

There are 3 ways resources can be re-mapped:
* With an Index
* Multiple with matches
* Multiple with fancy regex

### Re-map with an Index
The simplest method if you don't want to re-map that many resources.

```shell

```

### Match based re-mapping
Might be all you need when re-mapping multiple resources.
```shell

```

### Regex based re-mapping
Very advanced

```shell

```

## CLI args

| Short | Long | Description |
|-|-|-|
|-c| --config | Override LMMS' default configuration path. |
|-a| --auto | If a resource can be found with ``lmmsrc.xml``, its path will be replaced with an alias. <br> E.g. ``usersample``|

## Subcommands
When you need to do something quick and dirty.

| Short | Long | Description |
|-|-|-|
|-m| --match | Re-map project resources with simple string matching. |
|-r| --re | Re-map project resources with regular expresessions. |
|-o| --out | Specify the output file (when using the commands above). <br> (adding ``.mmpz`` will compress the project)|
||--list| List all of the resources and it associated instruments.|



# Compatibility
Should work across nearly all LMMS versions
