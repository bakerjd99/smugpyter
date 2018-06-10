# Refresh album CSV manifest files: assumes (smugpyter) location is on sys.path.
import smugpyter

smug = smugpyter.SmugPyter()
smug.download_smugmug_mirror(func_album=smug.write_album_manifest)
