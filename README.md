CLI tool to re-map paths in LMMS projects.


**Note**: You cannot edit resources of individual instruments.

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
First list out the resources:

```shell
python mmpa.py ./project.mmpz list
```

Use the information provided from that output to determine what resource to remap.

There are 2 ways resources can be re-mapped:
<!-- * With an Index -->
* With string matching
* With fancy regular expressions

<!-- ### Re-map with an Index
The simplest method if you don't want to re-map that many resources.

```shell

``` -->

### Match based re-mapping
Might be all you need when re-mapping multiple resources.

<!-- ```shell
mmpa.py ./test.mmpz --match


*List instruments*



what to match?: test.dll 

What to replace with?: hi.dll

``` -->

```shell
python mmpa.py ./test.mmpz match "C:\Users\Bob\Documents\LMMS\samples\" "usersample:" -o "test2.mmpz"
```

### Regex based re-mapping
Very advanced

```shell
TODO
```

## CLI args

| Short | Long | Description |
|-|-|-|
|-c| --config | Override LMMS' default configuration path. |
<!-- |-a| --auto | If a resource can be found with ``lmmsrc.xml``, its path will be replaced with an alias. <br> E.g. ``usersample``| -->

## Subcommands
When you need to do something quick and dirty.

| Long | Description |
|-|-|
| match | Re-map project resources with simple string matching. |
| re | Re-map project resources with regular expresessions. |
| -o/--out | Specify the output file (when using the commands above). <br> (adding ``.mmpz`` will compress the project)|
|list| List all of the resources and its associated instruments.|



# Compatibility
Should work across nearly all LMMS versions

Tested with python 3.8