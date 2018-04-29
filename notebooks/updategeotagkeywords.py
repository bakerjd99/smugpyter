# Update CSV geotagged keywords changes files. Run after 
# refreshing manifest files: assumes (smugpyter, geotagkeys) is on sys.path.
# After running this script apply the changes with (ChangeKeywords.bat)
# and then rerun (RefreshManifests.bat).

import geotagkeys

gk = geotagkeys.GeotagKeys()
root = 'c:\SmugMirror'

# update changes files
gk.yammer = True
print(gk.set_all_reverse_geocodes(root))