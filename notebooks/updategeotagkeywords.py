# Update CSV geotagged keywords changes files. Run after
# refreshing metadatea files: assumes (smugpyter, geotagkeys) is on sys.path.

import geotagkeys

gk = geotagkeys.GeotagKeys()

# update changes files
gk.yammer = True
print(gk.set_all_reverse_geocodes(gk.local_directory))
