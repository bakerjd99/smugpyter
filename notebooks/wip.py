# -*- coding: utf-8 -*-
"""
work in progress 
"""

import csv
import re
from collections import Iterable
import smugpyter

smugmug = smugpyter.SmugPyter()
smugmug.get_folders()

aspect_ratios = [0.7, 0.8, 0.755, 0.665, 0.5, 1, 0.745, 0.715, 
                 0.165, 0.4, 0.775, 0.75, 0.77]

print_areas = [[17.5,70],[20,80],[21.2,84.8],[24,96],[32,50,128],
               [25,64,100],[33.5],[35],[150 ],[160],[93.5],[108 ],[130]]

size_keywords = [['3.5x5','7x10'],['4x5','8x10'],['4x5.3','8x10.6'],
                 ['4x6','8x12'],['4x8','5x10', '8x16'],['5x5','8x8','10x10'],
                 ['5x6.7'],['5x7'],['5x30'],['8x20'],['8.5x11'],
                 ['9x12'],['10x13']]

def flatten(items):
    """Yield items from any nested iterable; see REF."""
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x

def round_to(n, precision):
    correction = 0.5 if n >= 0 else -0.5
    return int( n/precision+correction ) * precision

def aspect_ratio(height, width, *, precision=0.005):
    return round_to( min(height, width) / max(height, width), precision )

def dpi_area(height, width, *, dpi=360, precision=0.5):
    return round_to( (height * width) / dpi ** 2, precision )

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
        raise ValueError(error_message)
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
    outkeys = [size_keyword]
    inkeys = keywords.split(split_delimiter)
    for inword in inkeys:
        outword = inword.strip(' ').lower()
        # remove any existing print size keys
        if re.match(r"\d+(\.\d+)?[xz]\d+(\.\d+)?", outword) is not None:
            continue
        else:
            outkeys.append(outword)
    # return unique sorted keys
    outkeys = sorted(list(set(outkeys)))
    return (split_delimiter+' ').join(outkeys)

update_size_keyword('0z1', 'yo; a; list; of; keywords; 5x7; 4x5; 8x12; yada; yada')
update_size_keyword('0z1', '')

def print_keywords(manifest_file):
    """
    Set print size keywords for images in album manifest file.
    Result is a dictionary indexed by SmugMug image keys.
    """
    image_keywords = {}
    with open(manifest_file, 'r') as f:
        reader = csv.DictReader(f, dialect='excel', delimiter='\t')                     
        for row in reader:
            key = row['ImageKey']
            height , width = int(row['OriginalHeight']), int(row['OriginalWidth'])
            size_key = print_size_key(height, width)
            keywords = update_size_keyword(size_key, row['Keywords'])
            #print(key, size_key, height, width, keywords)
            image_keywords[key] = {'SizeKey':size_key, 'Height':height, 
                                   'Width':width, 'Keywords':keywords}
    return image_keywords

#print_keywords('c:\SmugMirror\Places\Overseas\Ghana1970s\manifest-Ghana1970s-Kng6tg.txt')
#
#
#
#with open('c:\SmugMirror\Places\Overseas\Ghana1970s\manifest-Ghana1970s-Kng6tg.txt', 'r') as f:
#    reader = csv.DictReader(f, dialect='excel', delimiter='\t')                     
#    for row in reader:
#        height , width = int(row['OriginalHeight']), int(row['OriginalWidth'])
#        print(row['ImageKey'], print_size_key(height, width), 
#              height, width, row['Keywords'].split(';'))    
#    
#list(flatten(size_keywords))
#    
#"; ".join(list(flatten(size_keywords)))
#sorted(('  boo FREAKING 77777 HOO hhhh ooo   '.strip(' ').lower()).split())

