# -*- coding: utf-8 -*-
import unittest
import printkeys

pk = printkeys.PrintKeys()

class PrintKeysTestCase(unittest.TestCase):
    
    def test_print_size_key_basic(self):
        self.assertEqual('0z0', pk.print_size_key(1,1))           # not enough pixels
        self.assertEqual('0z0', pk.print_size_key(20,20))         # not enough pixels
        self.assertEqual('0z0', pk.print_size_key(500,500))       # not enough pixels
        self.assertEqual('0z1', pk.print_size_key(2000,2100))     # ratio not in table
        self.assertEqual('0z1', pk.print_size_key(4000,3500))     # ratio not in table
        self.assertEqual('0z1', pk.print_size_key(1000,5000))     # ratio not in table
        self.assertEqual('0z0', pk.print_size_key(int(3.5 * 350), 5 * 350))     # 3.5x5 not enough pixels
        self.assertEqual('3.5x5', pk.print_size_key(int(3.5 * 362), 5 * 362))   # 3.5x5
        self.assertEqual('7x10', pk.print_size_key(7 * 362, 10 * 362))          # 7x10
        self.assertEqual('5x6.7', pk.print_size_key(5 * 362, int(6.7 * 362)))   # 5x6.7
        self.assertEqual('8.5x11', pk.print_size_key(int(8.5 * 362), 11 * 362)) # 8.5x11
        self.assertEqual('10x10', pk.print_size_key(10 * 362, 10 * 362))        # 10x10
        self.assertEqual('10x10', pk.print_size_key(10 * 722, 10 * 722, ppi=720)) # 10x10 at 720 DPI
        self.assertEqual('5x30', pk.print_size_key(5 * 362, 30 * 362))          # 5x30
        self.assertEqual('5x10', pk.print_size_key(5 * 722, 10 * 722, ppi=720)) # 5x10 at 720 DPI
        
    def test_print_size_key_exceptions(self):
        with self.assertRaises(TypeError):
            pk.print_size_key('not', 'even_wrong')
        with self.assertRaises(ValueError):
            pk.print_size_key(-2, -3)
        with self.assertRaises(ValueError):
            pk.print_size_key(0, 50)
        
if __name__ == '__main__':
    unittest.main()
    