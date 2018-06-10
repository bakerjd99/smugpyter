# Download new sample images: assumes (smugpyter) location is on sys.path.
# Run after refreshing manifest files.
import smugpyter

smug = smugpyter.SmugPyter()
#smug.yammer = True
#BUG: fix hard path: smug.local_directory
print(smug.update_all_sample_images(r'c:\SmugMirror\Mirror'))