# Scan CSV changes files in local directories and apply keyword changes.
# Run after refreshing manifest files and updating keyword changes files: 
# assumes (smugpyter) is on sys.path
import smugpyter

smug = smugpyter.SmugPyter()
print(smug.update_all_keyword_changes('c:\SmugMirror'))
