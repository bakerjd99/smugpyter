# Refresh album CSV manifest files: assumes (smugpyter) location is on sys.path.
import smugpyter

smugmug = smugpyter.SmugPyter()
smugmug.download_smugmug_mirror(func_album=smugmug.write_album_manifest)
