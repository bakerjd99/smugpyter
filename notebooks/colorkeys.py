# -*- coding: utf-8 -*-
import os
import csv
import webcolors
import numpy as np
import random
from PIL import Image
from math import sqrt
from sklearn.cluster import KMeans
import smugpyter

class ColorKeys(smugpyter.SmugPyter):
    
    dominant_prefix = "0_"
    reset_color_key = False
    resize_factor = 0.4
    num_clusters = 8
    
    # overly dominant colors - these colors will be
    # assigned to frequently by the default selection
    over_dominant = ['darkslategrey', 'black', 'dimgrey', 'darkgrey',
                     'grey', 'darkolivegreen', 'silver']
    
    # number between (0,1) - 0.10 means select roughly 10% of the time
    over_threshold = 0.10  
    
    
    def __init__(self):
        """ class constructor """
        super().__init__()
        
    
    def get_color_name(self, requested_color):
        """ 
        Return nearest named web color to the RGB tuple (requested_color).
        """
        try:
            rgb_distance = 0
            closest_name = actual_name = webcolors.rgb_to_name(requested_color)
        except ValueError:
            closest_name , rgb_distance = self.closest_color(requested_color)
            actual_name = None
        return (actual_name, closest_name, rgb_distance) 

        
    def cluster_name_freq_dist(self, image, *, num_clusters=8, factor=0.4):
        """
        Returns a tuple of sorted nearest named colors, cluster frequencies, and
        distances from cluster raw colors. Items are sorted by decreasing
        cluster frequency.
        
            ck = ColorKeys()
            image = Image.open('C:/SmugMirror/Themes/Manipulations/ImageHacking/hjbftwN-1-your-grainy-hell-awaits-[409595101].jpg')
            ck.cluster_name_freq_dist(image, num_clusters=8, factor=0.25)
        """
        km = KMeans(n_clusters=num_clusters)
        imcopy = self.resize_image(image, factor=factor)
        ar = np.asarray(imcopy)
        pixels = ar.reshape((-1, 3))
        km.fit(pixels)
        colors = np.asarray(km.cluster_centers_, dtype=np.uint8)
        frequencies = np.asarray(np.unique(km.labels_, return_counts = True)[1], dtype=np.int32)
        names = []
        distances = []
        for color in colors:
            _ , name , rgb_distance = self.get_color_name(color)
            names.append(name)
            distances.append(rgb_distance)
        # order by decreasing frequency
        _ , names = self.dualsort(frequencies, names, reverse=True)
        frequencies , distances = self.dualsort(frequencies, distances, reverse=True)
        return (names, frequencies, distances)
    
    
    def dominant_color_key(self, names_freqs_dists):
        """
        Return a single dominant color key.
        """
        names , frequencies , distances = names_freqs_dists
        
        if  len(names) <= 1:
             raise ValueError('need at least two named colors') 
        
        if len(names) > len(list(set(names))):
            # most frequent repeated named color
            key = self.most_common(names)
        else:
            # distances less greatest outlier
            dist_sample = sorted(distances, reverse=True)[1:]
            threshold = np.mean(dist_sample) + np.std(dist_sample)
            
            # default color choice
            key = names[0]
            
            # return first color from sorted names that is no more
            # than one standard deviation from the sample mean. If
            # no such choice is made retain the default selection.
            for name, distance in zip(names, distances): 
                if distance <= threshold:
                    key = name
                    break
         
        roll = random.random()   
        if (key in self.over_dominant) and (self.over_threshold < roll):
            # these keys appear to frequently
            # select another color a certain % of time
            ix = names.index(key)
            if (1 + ix) < len(names):
                key = names[ix + 1]
                
        return self.dominant_prefix + key.lower().strip()
    
    
    def color_keywords(self, manifest_file, *, split_delimiter=';'):
        """
        Set color keywords for images in album manifest file.
        Result is a tuple (image_count, change_count, changed_keywords).
        (changed_keyords) is a list of dictionaries in (csv.DictWriter) format.
        
            ck = ColorKeys()
            manifest_file = 'c:\SmugMirror\Places\Overseas\Ghana1970s\manifest-Ghana1970s-Kng6tg-w.txt'
            ck.color_keywords(manifest_file)
        """
        changes_dict = {}
        if self.merge_changes:
            changes_file = self.changes_filename(manifest_file)
            changes_dict = self.image_dict_from_csv(changes_file)
        merge_keys = self.merge_changes and 0 < len(changes_dict)
          
        image_path = self.image_path_from_file(manifest_file)                                       
        changed_keywords = []
        image_count , change_count = 0 , 0
        with open(manifest_file, 'r') as f:
            reader = csv.DictReader(f, dialect='excel', delimiter='\t')                     
            for row in reader:
                image_count += 1
                key = row['ImageKey']
                inwords = row['Keywords']
                
                # do not reset extant color keys unless (reset_color_key) is true
                if self.dominant_prefix in inwords:
                    if not self.reset_color_key:
                        continue
                
                # merge in current changes file keywords
                if merge_keys:
                    if key in changes_dict:
                        inwords = inwords + split_delimiter + changes_dict[key]['Keywords']
                        
                # check existence of alleged image file
                new_name = self.image_file_name(key, row['FileName'])
                #print(new_name)
                image_file_name = image_path + new_name
                if not os.path.isfile(image_file_name):
                    error_message = "image file missing -> " + image_file_name
                    self.append_to_log(error_message)
                    continue
                
                # read sample image file and compute color key
                image = Image.open(image_file_name)
                try:
                    names_freqs_dists = self.cluster_name_freq_dist(image, 
                                                                    num_clusters=self.num_clusters,
                                                                    factor=self.resize_factor)
                except:
                    # some images cannot be processed - log for inspection
                    error_message = "cannot compute color key -> " + image_file_name
                    self.append_to_log(error_message)
                    continue
                
    
                color_key = self.dominant_color_key(names_freqs_dists)
                same, keywords = self.update_keywords(color_key, 
                                                      inwords,
                                                      key_pattern=r"\d+?[_]",
                                                      split_delimiter=split_delimiter)
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
    
        
    def write_color_keyword_changes(self, manifest_file):
        """
        Write TAB delimited file of changed color keywords.
        Return album and keyword (image_count, change_count) tuple.
        
            ck = ColorKeys()
            manifest_file = 'c:\SmugMirror\Places\Overseas\Ghana1970s\manifest-Ghana1970s-Kng6tg-w.txt'
            ck.write_color_keyword_changes(manifest_file)  
        """
        return self.write_keyword_changes(manifest_file, func_keywords=self.color_keywords)
    
    
    def update_all_color_keyword_changes(self, root):
        """
        Scan all manifest files in local directories and
        generate TAB delimited CSV print size keyword changes files.
        
            ck = ColorKeys()
            ck.update_all_color_keyword_changes('c:\SmugMirror')
        """
        return self.scan_do_local_files(root, func_do=self.write_color_keyword_changes)
                

    @staticmethod
    def most_common(lst):
        """ Pick most common item in a list - ok for small lists."""
        return max(set(lst), key=lst.count)
    
    
    @staticmethod
    def closest_color(requested_color):
        """ Nearest named web color using Euclidean metric."""
        min_colors = {}
        for key, name in webcolors.css3_hex_to_names.items():
            r_c, g_c, b_c = webcolors.hex_to_rgb(key)
            rd = (r_c - requested_color[0]) ** 2
            gd = (g_c - requested_color[1]) ** 2
            bd = (b_c - requested_color[2]) ** 2
            min_colors[(rd + gd + bd)] = name
        return (min_colors[min(min_colors.keys())], sqrt(min(min_colors.keys()))) 
    
    
    @staticmethod
    def resize_image(image, *, factor=0.4, small_side=100):
        """Resize PIL image maintaining aspect ratio."""
        imcopy = image.copy()
        
        # do not resize very small images
        if max(imcopy.size) < small_side:
            return imcopy
        
        #print(imcopy.size)
        width, height = imcopy.size
        width = int(factor * width)
        height = int(factor * height) 
        return imcopy.resize((width, height))


#if __name__ == '__main__':
#    ck = ColorKeys()
#    
#    image1 = Image.open('C:/SmugMirror/Themes/Manipulations/ImageHacking/5NB7dXP-1f-green-gray-dragon-eggs.jpg')
#    image2 = Image.open('C:/SmugMirror/Themes/Manipulations/ImageHacking/hjbftwN-1-your-grainy-hell-awaits-[409595101].jpg')
#    
#    names_freqs_dists1 = ck.cluster_name_freq_dist(image1)
#    names_freqs_dists2 = ck.cluster_name_freq_dist(image2)
#
#    print(ck.dominant_color_key(names_freqs_dists1))
#    print(ck.dominant_color_key(names_freqs_dists2))
#
#    ck.yammer = True
#    manifest_file = 'C:\SmugMirror\Themes\Diaries\CellPhoningItIn\manifest-CellPhoningItIn-PfCsJz-16.txt'
#    ck.write_keyword_changes(manifest_file, ck.color_keywords)
#    
#    ck.update_all_color_keyword_changes('c:\SmugMirror')

