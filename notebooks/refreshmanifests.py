# refresh album CSV manifest files
# assumes (smugpyter) location is on sys.path
import smugpyter

smugmug = smugpyter.SmugPyter()
smugmug.download_smugmug_mirror()