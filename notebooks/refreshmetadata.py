# Refresh album TAB delimited files: assumes (smugpyter) location is on sys.path.
import smugpyter

smug = smugpyter.SmugPyter()
smug.download_album_metadata()
