# -*- coding: utf-8 -*-

import smugpyter

class PrintKeys(smugpyter.SmugPyter):
    
    def __init__(self, verbose=False):
        
        super().__init__(verbose)
        
        self.smug_default_sizes = """
 3.5x5  4x5    4x5.3  4x6    4x8    
 5x5    5x6.7  5x7    5x10   5x30   
 7x10   8x8    8x10   8x10.6 8x12   
 8x16   8x20   8.5x11 9x12   10x10  
 10x13  10x15  10x16  10x20  10x30  
 11x14  11x16  11x28  12x12  12x18  
 12x20  12x24  12x30  16x20  16x24  
 18x24  20x20  20x24  20x30 
"""

        self.smug_print_sizes = self.purify_smugmug_text(self.smug_default_sizes).split()
    
#    def set_aspect_ratios(self, smug_print_sizes):
#        all_aspect_ratios = []
#        all_print_areas = []
#
#        for size in smug_print_sizes:
#            height , width = size.split('x')
#            height = float(height) 
#            width = float(width)
#            ratio = aspect_ratio(height, width)
#            area = height * width
#            all_aspect_ratios.append(ratio)
#            all_print_areas.append(area)
#    
#        return list(set(all_aspect_ratios))

   
    