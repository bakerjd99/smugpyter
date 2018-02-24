# Refresh album CSV real date files:
# assumes (smugpyter) location is on sys.path

# WARNING: it takes a long time to run this script for the
# first time. The dates we are looking for are buried in the
# original EXIF/IPTC image values and there appears to be no fast
# way to extract these dates using the SmugMug API 2.0.
# The "fast" API dates are upload and change dates which
# are not image EXIF dates. You have to ping the metadata 
# of every single image in all albums to extract "real dates."
# The good news is that these dates are fairly stable and 
# simple caching of previously fetched dates works well
# for typical incremental updates.

import smugpyter

smug = smugpyter.SmugPyter(yammer=True)
smug.download_smugmug_mirror(func_album=smug.write_album_real_dates)
