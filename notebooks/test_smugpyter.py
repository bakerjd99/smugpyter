# -*- coding: utf-8 -*-
import smugpyter
import unittest

smug = smugpyter.SmugPyter()

class SmugPyterTestCase(unittest.TestCase):
    
    def test_image_path_from_file_basic(self):
        self.assertEqual('c:\\boo\\hoo\\', smug.image_path_from_file('c:\\boo\\hoo\\test.txt'))
        self.assertEqual('c:/yeah/so/', smug.image_path_from_file('c:/yeah/so/what.txt'))
        
          
    def test_image_path_from_file_exceptions(self):
        with self.assertRaises(ValueError):
            smug.image_path_from_file('c:\\this/is\\so/wrong.txt')  # only one path delimiter
      
        
if __name__ == '__main__':
    unittest.main()
    