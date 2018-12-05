# Refresh album TAB delimited files of recently changed online galleries.
import smugpyter

smug = smugpyter.SmugPyter()

# smug.days_before set in config 
smug.download_album_metadata(smug.days_before)
