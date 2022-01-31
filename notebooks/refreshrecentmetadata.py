# Refresh album TAB delimited files of recently changed online galleries.
import sys
sys.path.append(r'C:\mp\jupyter\smugpyter\notebooks')

import smugpyter

smug = smugpyter.SmugPyter()

# smug.days_before set in config 
smug.download_album_metadata(smug.days_before)
