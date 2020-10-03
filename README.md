# find-dup-files
Find Duplicate Files

Quite often, we get files duplicated on our storage devices. This could result
from multiple backups, or variety of other reasons. This set of scripts give 
some help in identifying duplicate files.  

# Setup

### PIP based

``` 
pip install -r requirements.txt
```

### Conda based
```
conda env create -n <envname> environment.yml
```

# How to use
### Collect information
```
prepare-index.py prepare [-h] [--dir Directory] [--ext Opt-Extension]
                              [--index Index-yaml] [--verbose]
```

| Knob | Meaning |
| ----- | -------- |
|```--dir Directory``` | Directory to be searched, defaults to "." |
|```--ext Opt-Extension``` | (Optional) File Extension to limit search to. All files considered without this knob |
|```--index Index-Yaml``` | Name of output yaml file storing the file index, defaults to "index.yaml" |

### Show duplicate file details
```
dups-analyze.py [-h] [--verbose] [--head number-of-directory-pairs]
                       [--index Index-yaml] [--verbose]
``` 
| Knob | Meaning |
| ----- | -------- |
|```--index Index-Yaml``` | Name of output yaml file storing the file index, defaults to "index.yaml" |
|```--head num``` | Limit output to num pairs. All pairs displayed without this knob |
|```--verbose``` | Usual output shows pairs of directories having duplicate files. Verbose knob enables details of files as well |

### Output of dups-analyze

This script outputs one line for each pair of directories which have some duplicate files.
Output is sorted on the descending order of number of bytes of duplicate data in the directory.
This ensures that the two directories having the largest number of duplicated bytes is listed first.
The ```--head num``` knob limits the output to the top ```num``` lines.

The optional ```--verbose``` knob lists the duplicated files within each directory-pair. This list
of files is suppressed by default.
  

