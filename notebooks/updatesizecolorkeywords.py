# Update CSV print size and color keywords changes files.
# Run after refreshing metadata files and updating sample images.
# Assumes (smugpyter, printkeys, colorkeys) are on sys.path.

import printkeys
import colorkeys

# both subclasses of SmugPyter
pk = printkeys.PrintKeys()
ck = colorkeys.ColorKeys()

# local directory in config - set in superclass
root = pk.local_directory

# update changes files - order matters
#pk.yammer = True
#pk.merge_changes = True
print(pk.update_all_size_keyword_changes(root))

#ck.yammer = True
ck.merge_changes = True
print(ck.update_all_color_keyword_changes(root))