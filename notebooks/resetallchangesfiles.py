# Empty all CSV changes files: assumes (smugpyter) location is on sys.path.
import smugpyter

smug = smugpyter.SmugPyter()
print(smug.reset_all_changes_files(smug.local_directory))
