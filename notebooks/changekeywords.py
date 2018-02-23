# Scan CSV changes files in local directories and apply keyword changes.
# Run after refreshing manifest files and updating keyword changes files: 
# assumes (smugpyter, printkeys) is on sys.path
import printkeys

pk = printkeys.PrintKeys()
pk.update_all_keyword_changes('c:\SmugMirror')
