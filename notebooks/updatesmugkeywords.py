# Update CSV TAB delimited geotag, print size and color keyword 
# changes files. Run after refreshing metadata files and updating
# sample images. Assumes (smugpyter, geotagkeys, printkeys, colorkeys)
# are on sys.path.

import geotagkeys
import printkeys
import colorkeys

# subclasses of SmugPyter
gk = geotagkeys.GeotagKeys(log_start=True)
pk = printkeys.PrintKeys()
ck = colorkeys.ColorKeys(verbose=True)

# local directory in config - set in superclass
root = pk.local_directory

# reset all changes files
print(gk.reset_all_changes_files(root))

# update changes files - order matters
print(gk.update_all_geotag_keyword_changes(root))

pk.merge_changes = True
print(pk.update_all_size_keyword_changes(root))

ck.merge_changes = True
print(ck.update_all_color_keyword_changes(root))