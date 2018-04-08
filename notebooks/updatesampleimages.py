# Download new sample images: assumes (smugpyter) location is on sys.path.
# Run after refreshing manifest files.
import smugpyter

smug = smugpyter.SmugPyter()
#smug.yammer = True
print(smug.update_all_sample_images('c:\SmugMirror'))