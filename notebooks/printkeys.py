# -*- coding: utf-8 -*-
import re
import csv
import os
import smugpyter

class PrintKeys(smugpyter.SmugPyter):
    
    smug_default_sizes = """
 3.5x5  4x5    4x5.3  4x6    4x8    
 5x5    5x6.7  5x7    5x10   5x30   
 7x10   8x8    8x10   8x10.6 8x12   
 8x16   8x20   8.5x11 9x12   10x10  
 10x13  10x15  10x16  10x20  10x30  
 11x14  11x16  11x28  12x12  12x18  
 12x20  12x24  12x30  16x20  16x24  
 18x24  20x20  20x24  20x30 
"""
  
    # print size key lists
    aspect_ratios = None
    print_areas = None
    size_keywords = None
    
    def __init__(self, verbose=False):
        
        super().__init__(verbose)

        self.smug_print_sizes = self.purify_smugmug_text(self.smug_default_sizes).split()
        
        (self.aspect_ratios, self.print_areas, self.size_keywords) = self.set_print_sizes(self.smug_print_sizes)
        
    def aspect_ratio(self, height, width, *, precision=0.005):
        return self.round_to( min(height, width) / max(height, width), precision )

    def dpi_area(self, height, width, *, dpi=360, precision=0.5):
        return self.round_to( (height * width) / dpi ** 2, precision )   
  
    def set_print_sizes(self, smug_print_sizes):
        """
        Sets the lists that represent the print sizes table.
        Result is a tuble of lists (aspect_ratios, print_areas, size_keywords).
        """
        all_aspect_ratios = []
        all_print_areas = []
        for size in smug_print_sizes:
            height , width = size.split('x')
            height = float(height) 
            width = float(width)
            ratio = self.aspect_ratio(height, width)
            area = height * width
            all_aspect_ratios.append(ratio)
            all_print_areas.append(area)
        aspect_ratios = list(set(all_aspect_ratios))
        
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
            # insure sublists are sorted by ascending area
            gp , gk = self.dualsort(gp, gk)
            gpa.append(gp)
            gsk.append(gk)
        print_areas = gpa
        size_keywords = gsk
        
        return (aspect_ratios, print_areas, size_keywords)
    
    def print_size_key(self, height, width, *, no_ratio='0z1', no_pixels='0z0', 
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
        print_area = self.dpi_area(height, width, dpi=ppi)
        if print_area < min_area:
            return no_pixels
    
        print_ratio = self.aspect_ratio(height, width)
        print_key = no_ratio
        for i, ratio in enumerate(self.aspect_ratios):
            if abs(print_ratio - ratio) <= tolerance:
                print_key = no_pixels
            
            # not enough or more than enough area
            if print_area < self.print_areas[i][0]:
                break
            elif print_area > self.print_areas[i][-1]:
                print_key = self.size_keywords[i][-1]
                break     
            
            for j, area in enumerate(self.print_areas[i]):
                if area >= print_area and 0 < j:
                    print_key = self.size_keywords[i][j - 1]
                    break
                    
        return print_key
    
    def update_size_keyword(self, size_keyword, keywords, split_delimiter=';'):
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
                
        # return standard unique sorted keys
        outkeys = sorted(list(set(outkeys)))
        outkeys = self.standard_keywords(split_delimiter.join(outkeys))
        return (set(outkeys) == set(inkeys), (split_delimiter+' ').join(outkeys))
    
    def print_keywords(self, manifest_file):
        """
        Set print size keywords for images in album manifest file.
        Result is a tuple (image_count, change_count, changed_keywords).
        (changed_keyords) is a list of dictionaries in (csv.DictWriter) format.
        """
        changed_keywords = []
        image_count , change_count = 0 , 0
        with open(manifest_file, 'r') as f:
            reader = csv.DictReader(f, dialect='excel', delimiter='\t')                     
            for row in reader:
                image_count += 1
                key = row['ImageKey']
                height , width = int(row['OriginalHeight']), int(row['OriginalWidth'])
                size_key = self.print_size_key(height, width)
                same, keywords = self.update_size_keyword(size_key, row['Keywords'])
                if not same:
                    change_count += 1
                    changed_keywords.append({'ImageKey': key, 'AlbumKey': row['AlbumKey'],
                                           'FileName': row['FileName'], 'Keywords': keywords,
                                           'OldKeywords': row['Keywords']})
                    
        # when no images are changed return a header place holder row
        if change_count == 0:
            changed_keywords.append({'ImageKey': None, 'AlbumKey': None, 'FileName': None, 
                                     'Keywords': None, 'OldKeywords': None})
            
        return (image_count, change_count, changed_keywords)
    
    def album_id_from_file(self, filename):
        """
        Extracts the (album_id, name, mask) from file names. 
        Depends on file naming conventions.
        
            album_id_from_file('c:\SmugMirror\Places\Overseas\Ghana1970s\manifest-Ghana1970s-Kng6tg-w.txt')    
        """
        mask, album_id, name = filename.split('-')[::-1][:3]
        mask = mask.split('.')[0]
        return (self.case_mask_decode(album_id, mask), name, mask)
    
    def changes_filename(self, manifest_file):
        """
        Changes file name from manifest file name.
        """
        album_id, name, mask = self.album_id_from_file(manifest_file)
        path = os.path.dirname(manifest_file)
        changes_name = "changes-%s-%s-%s" % (name, album_id, mask)
        changes_file = path + "/" + changes_name + '.txt'
        return changes_file
    
    def write_size_keyword_changes(self, manifest_file):
        """
        Write TAB delimited file of changed metadata.
        Return album and keyword (image_count, change_count) tuple.
        
            manifest_file = 'c:\SmugMirror\Places\Overseas\Ghana1970s\manifest-Ghana1970s-Kng6tg-w.txt'
            write_size_keyword_changes(manifest_file)  
        """
        image_count, change_count, keyword_changes = self.print_keywords(manifest_file)
        changes_file = self.changes_filename(manifest_file)
        keys = keyword_changes[0].keys()
        with open(changes_file, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys, dialect='excel-tab')
            dict_writer.writeheader()
            # for no changes write header only
            if change_count > 0:
                dict_writer.writerows(keyword_changes)    
        return(image_count, change_count)
        
    def update_all_keyword_changes_files(self, root):
        """
        Scan all manifest files in local directories and
        generate TAB delimited CSV keyword changes files.
        """
        total_images , total_changes = 0 , 0
        pattern = "manifest-"
        alist_filter = ['txt'] 
        for r,d,f in os.walk(root):
            for file in f:
                if file[-3:] in alist_filter and pattern in file:
                    file_name = os.path.join(root,r,file)
                    image_count, change_count = self.write_size_keyword_changes(file_name)
                    if change_count > 0:
                        print(file_name)
                    total_images += image_count
                    total_changes += change_count
        print('image count %s, change count %s' % (total_images, total_changes))
    
    @staticmethod
    def standard_keywords(keywords, *, blank_fill='_', 
                      split_delimiter=';',
                      substitutions=[('united_states','usa')]):
        """
        Return a list of keywords in standard form.
        
        Reduces multiple blanks to one, converts to lower case, and replaces
        any remaining blanks with (blank_fill). This insures keywords are contigous
        lower case or hypenated lower case character runs.
        
        Note: the odd choice of '_' for the blank fill is because hyphens appear
        to be stripped from keywords on SmugMug.
        
            standard_keywords('go;ahead;test me;boo    hoo  ; you   are   so; 0x0; united   states')
        """
    
        # basic argument check
        error_message = '(keywords) must be a string'
        if not isinstance(keywords, str):
            raise TypeError(error_message)
        
        if len(keywords.strip(' ')) == 0:
            return []
        else:
            keys = ' '.join(keywords.split())                         
            keys = split_delimiter.join([s.strip().lower() for s in keys.split(split_delimiter)])
            keys = ''.join(blank_fill if c == ' ' else c for c in keys)
            # replace some keywords with others
            for k, s in substitutions:
                keys = keys.replace(k, s)
            # return sorted list - move size keys to front     
            keylist = [s for s in keys.split(split_delimiter)]
            return sorted(keylist)
    
    @staticmethod
    def dualsort(a, b):
        """
        Sort lists (a) and (b) using (a) to grade (b).
        """
        temp = sorted(zip(a, b), key=lambda x: x[0])
        return list(map(list, zip(*temp)))
    
    @staticmethod
    def round_to(n, precision):
        correction = 0.5 if n >= 0 else -0.5
        return int( n/precision+correction ) * precision
    