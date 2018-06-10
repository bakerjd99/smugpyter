# Update CSV print size keywords changes files.
# Run after refreshing manifest files and updating
# sample images: assumes (smugpyter, printkeys,
# colorkeys, geotagkeys) are on sys.path.

import printkeys
import colorkeys

pk = printkeys.PrintKeys()
ck = colorkeys.ColorKeys()
root = r'c:\SmugMirror\Mirror'

# update changes files - order matters
#pk.yammer = True
#pk.merge_changes = True
print(pk.update_all_size_keyword_changes(root))

#ck.yammer = True
ck.merge_changes = True
print(ck.update_all_color_keyword_changes(root))

# change online keywords
print(pk.update_all_keyword_changes(root))
