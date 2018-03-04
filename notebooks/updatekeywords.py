# Update CSV print size keywords changes files.
# Run after refreshing manifest files: assumes 
# (smugpyter, printkeys, geotagkeys) is on sys.path.
import printkeys
import geotagkeys

gk = geotagkeys.GeotagKeys()
pk = printkeys.PrintKeys()
root = 'c:\SmugMirror'

# update changes files - order matters
gk.set_all_reverse_geocodes(root)
pk.yammer = True
pk.merge_changes = True
pk.update_all_keyword_changes_files(root)

# change online keywords
# pk.update_all_keyword_changes(root)
