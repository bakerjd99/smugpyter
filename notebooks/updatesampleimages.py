# Download new sample images: assumes (smugpyter) location is on sys.path.
# Run after refreshing metadata files.
import smugpyter

smug = smugpyter.SmugPyter()
#smug.yammer = True
print(smug.update_all_sample_images(smug.local_directory))