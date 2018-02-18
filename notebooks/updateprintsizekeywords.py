# update CSV print size keywords changes files.
# run after refreshing manifest files.
# assumes (smugpyter, printkeys)  is on sys.path
import printkeys

pk = printkeys.PrintKeys()
pk.update_all_keyword_changes_files('c:\SmugMirror')
