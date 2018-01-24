# -*- coding: utf-8 -*-
"""
work in progress 
"""

import os
import csv
import re
from collections import Iterable
import smugpyter


smugmug = smugpyter.SmugPyter()

# list of all known small to medium SmugMug print sizes
smug_print_sizes = """
 3.5x5  4x5    4x5.3  4x6    4x8    
 5x5    5x6.7  5x7    5x10   5x30   
 7x10   8x8    8x10   8x10.6 8x12   
 8x16   8x20   8.5x11 9x12   10x10  
 10x13  10x15  10x16  10x20  10x30  
 11x14  11x16  11x28  12x12  12x18  
 12x20  12x24  12x30  16x20  16x24  
 18x24  20x20  20x24  20x30 
"""

# clean up the usual suspects
smug_print_sizes = smugmug.purify_smugmug_text(smug_print_sizes).split()
print(smug_print_sizes)

def round_to(n, precision):
    correction = 0.5 if n >= 0 else -0.5
    return int( n/precision+correction ) * precision

def aspect_ratio(height, width, *, precision=0.005):
    return round_to( min(height, width) / max(height, width), precision )

def dpi_area(height, width, *, dpi=360, precision=0.5):
    return round_to( (height * width) / dpi ** 2, precision )


all_aspect_ratios = []
all_print_areas = []

for size in smug_print_sizes:
    height , width = size.split('x')
    height = float(height) 
    width = float(width)
    ratio = aspect_ratio(height, width)
    area = height * width
    all_aspect_ratios.append(ratio)
    all_print_areas.append(area)
    
aspect_ratios = list(set(all_aspect_ratios))
print(aspect_ratios)

# group areas and keys by ratios
gpa = []
gsk = []
for ur in aspect_ratios:
    gp = []
    gk = []
    for ar, pa, sk in zip(all_aspect_ratios, all_print_areas, smug_print_sizes):
        if ur == ar:
            gp.append(pa)
            gk.append(sk)
    gpa.append(gp)
    gsk.append(gk)
    
print_areas = gpa
size_keywords = gsk

print(aspect_ratios)
print(len(aspect_ratios))

print(print_areas)
print(len(print_areas))


def flatten(items):
    """Yield items from any nested iterable; see REF."""
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x
            
min_print_area = min(list(flatten(print_areas)))
print(min_print_area)

smugmug.get_folders()

# aspect_ratios = [0.7, 0.8, 0.755, 0.665, 0.5, 1, 0.745, 0.715, 
                 # 0.165, 0.4, 0.775, 0.75, 0.77]

# print_areas = [[17.5,70],[20,80],[21.2,84.8],[24,96],[32,50,128],
               # [25,64,100],[33.5],[35],[150 ],[160],[93.5],[108 ],[130]]

# size_keywords = [['3.5x5','7x10'],['4x5','8x10'],['4x5.3','8x10.6'],
                 # ['4x6','8x12'],['4x8','5x10', '8x16'],['5x5','8x8','10x10'],
                 # ['5x6.7'],['5x7'],['5x30'],['8x20'],['8.5x11'],
                 # ['9x12'],['10x13']]

			
print(size_keywords)
print(len(size_keywords))

def print_size_key(height, width, *, no_ratio='0z1', no_pixels='0z0', 
                   min_area=17.5, ppi=360, tolerance=0.000005):
    """
    Compute print size key word from image dimensions. 
    The result is a character string.
    
      key360 = print_size_key(2000, 3000)
      
      # (ppi) is identical to dpi here
      key720 = print_size_key(2000, 3000, ppi=720) 
    """
    
    # basic argument check
    error_message = '(height), (width) must be positive integers'
    if not (isinstance(height, int) and isinstance(width, int)):
        raise TypeError(error_message)
    elif height <= 0 or width <= 0:
        raise ValueError(error_message)
    
    # area must exceed a minimum size
    print_area = dpi_area(height, width, dpi=ppi)
    if print_area < min_area:
        return no_pixels
    
    print_ratio = aspect_ratio(height, width)
    print_key = no_ratio
    for i, ratio in enumerate(aspect_ratios):
        if abs(print_ratio - ratio) <= tolerance:
            print_key = no_pixels
            
            # not enough or more than enough area
            if print_area < print_areas[i][0]:
                break
            elif print_area > print_areas[i][-1]:
                print_key = size_keywords[i][-1]
                break     
            
            for j, area in enumerate(print_areas[i]):
                if area >= print_area and 0 < j:
                    print_key = size_keywords[i][j - 1]
                    break
                    
    return print_key
	
def update_size_keyword(size_keyword, keywords, split_delimiter=';'):
    """
    Update the print size keyword for a single image
    and standardize the format of any remaining keywords.
    Result is a (boolean, string) tuple.
    """
    # basic argument check
    error_message = '(size_keyword), (keywords) must be nonempty strings'
    if not (isinstance(size_keyword, str) and isinstance(keywords, str)):
        raise TypeError(error_message)
    elif len(size_keyword.strip(' ')) == 0:
        raise ValueError(error_message)
        
    if len(keywords.strip(' ')) == 0:
        return (False, size_keyword)
    
    inkeys = [s.strip().lower() for s in keywords.split(split_delimiter)]
    if 0 == len(inkeys):
        return (False, size_keyword)
    
    outkeys = [size_keyword]
    for inword in inkeys:
        # remove any existing print size keys
        if re.match(r"\d+(\.\d+)?[xz]\d+(\.\d+)?", inword) is not None:
            continue
        else:
            outkeys.append(inword)
            
    # return unique sorted keys
    outkeys = sorted(list(set(outkeys)))
    return (set(outkeys) == set(inkeys), (split_delimiter+' ').join(outkeys))
	
def print_keywords(manifest_file):
    """
    Set print size keywords for images in album manifest file.
    Result is a list of dictionaries in (csv.DictWriter) format.
    """
    changed_keywords = []
    image_count = 0
    with open(manifest_file, 'r') as f:
        reader = csv.DictReader(f, dialect='excel', delimiter='\t')                     
        for row in reader:
            image_count += 1
            key = row['ImageKey']
            height , width = int(row['OriginalHeight']), int(row['OriginalWidth'])
            size_key = print_size_key(height, width)
            same, keywords = update_size_keyword(size_key, row['Keywords'])
            if not same:
                changed_keywords.append({'ImageKey': key, 'AlbumKey': row['AlbumKey'],
                                       'FileName': row['FileName'], 'Keywords': keywords,
                                       'OldKeywords': row['Keywords']})
    return (image_count, changed_keywords)

def album_id_from_file(filename):
    """
    Extracts the (album_id, name, mask) from file names. 
    Depends on file naming conventions.
    
        album_id_from_file('c:\SmugMirror\Places\Overseas\Ghana1970s\manifest-Ghana1970s-Kng6tg-w.txt')    
    """
    mask, album_id, name = filename.split('-')[::-1][:3]
    mask = mask.split('.')[0]
    return (smugmug.case_mask_decode(album_id, mask), name, mask)

#manifest_file = 'c:\SmugMirror\Places\Overseas\Ghana1970s\manifest-Ghana1970s-Kng6tg-w.txt'
#album_id_from_file(manifest_file)
	
def write_keyword_changes(manifest_file):
        """
        Write TAB delimited file of changed metadata.
        Return album and keyword (image_count, change_count) tuple.
        """
        image_count, keyword_changes = print_keywords(manifest_file)
        change_count = len(keyword_changes)
        if change_count == 0:
            return (image_count, 0)
            
        album_id, name, mask = album_id_from_file(manifest_file)
        path = os.path.dirname(manifest_file)
        
        changes_name = "changes-%s-%s-%s" % (name, album_id, mask)
        changes_file = path + "/" + changes_name + '.txt'
        
        keys = keyword_changes[0].keys()
        with open(changes_file, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys, dialect='excel-tab')
            dict_writer.writeheader()
            dict_writer.writerows(keyword_changes)
            
        return(image_count, change_count)
            
#write_keyword_changes(manifest_file)

def update_all_keyword_changes(root):
    """
    Scan all manifest files in local directories and
    generate TAB delimited CSV keyword changes files.
        
        update_all_keyword_changes('c:\SmugMirror')
    """
    total_images , total_changes = 0 , 0
    pattern = "manifest-"
    alist_filter = ['txt'] 
    for r,d,f in os.walk(root):
        for file in f:
            if file[-3:] in alist_filter and pattern in file:
                image_count, change_count = write_keyword_changes(os.path.join(root,r,file))
                total_images += image_count
                total_changes += change_count
    print('image count %s, change count %s' % (total_images, total_changes))