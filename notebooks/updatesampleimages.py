# download new sample images
# Run after refreshing metadata files.
import sys
sys.path.append(r'C:\mp\jupyter\smugpyter\notebooks')

import smugpyter

smug = smugpyter.SmugPyter()
#smug.yammer = True
print(smug.update_all_sample_images(smug.local_directory))