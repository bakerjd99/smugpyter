# -*- coding: utf-8 -*-
import csv
import os
import smugpyter

class GeotagKeys(smugpyter.SmugPyter):
    
    def __init__(self, verbose=False):
        
        super().__init__(verbose)


    def geotag_images(self, manifest_file, *, split_delimiter=';', geotag_key='geotagged'):
        """
        Sets a geotagged keyword for nongeotagged images with nonzero latitude or longitude.
        """
        change_count = 0
        with open(manifest_file, 'r') as f:
            reader = csv.DictReader(f, dialect='excel', delimiter='\t')                     
            for row in reader:
                key = row['ImageKey']
                latitude = float(row['Latitude'])
                longitude = float(row['Longitude'])
                if latitude != 0.0 or longitude != 0.0:
                    keywords = row['Keywords']
                    inkeys = [s.strip().lower() for s in keywords.split(split_delimiter)]
                    
                    # if an image is already geotagged skip it 
                    if geotag_key in inkeys:
                        continue
                        
                    outkeys = list(set(inkeys))
                    outkeys.append(geotag_key)
                    outkeys = sorted(outkeys)
                    new_keywords = (split_delimiter+' ').join(outkeys)
                    outkeys = self.standard_keywords(new_keywords, split_delimiter=split_delimiter) 
                    same, new_keywords = (set(outkeys) == set(inkeys), (split_delimiter+' ').join(outkeys))
                    if not same:
                        change_count += 1   
                        #print(manifest_file)
                        #print(key, new_keywords)
                        self.change_image_keywords(key, new_keywords)
        return change_count
    
    
    def set_all_geotags(self, root):
        """
        Scan all manifest files in local directories and set
        geotags for images with nonzero latitude or longitude
        that are not geotagged.
        """
        total_changes = 0
        pattern = "manifest-"
        alist_filter = ['txt'] 
        for r,d,f in os.walk(root):
            for file in f:
                if file[-3:] in alist_filter and pattern in file:
                    file_name = os.path.join(root,r,file)
                    change_count = self.geotag_images(file_name)
                    if change_count > 0:
                        print(file_name)
                    total_changes += change_count
        print('change count %s' % total_changes)