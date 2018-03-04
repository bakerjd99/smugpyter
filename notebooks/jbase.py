"""
usage:
 jbase.init(True)  # True (default) loads profile - False avoids
 
 jbase.dor('i.2 3 4')    # run sentence and print output result
 jbase.do(('+a.')        # run and return error code
 jbase.getr()            # get last output result
 jbase.do('abc=: i.2 3') # define abc
 q= jbase.get('abc')     # get q as numpy array from J array 
 jbase.set('ghi',23+q)   # set J array from numpy array
 jbase.jdor('ghi')       # print array 
 jbase.j()               # J repl - .... to exit

types:
 python types supported: strings, bytes, numpy int64/float64 
 numpy arrays have shape
 json covers some other requirements
 
Developed with Python 3.6.4 (Anaconda) and J807.

Works with python kernel in Jupyiter.

"""

# start python3, import jbase, print(jbase.__doc__)

# put copy of this file (jbase.py) where python3 can find it
# do required editing of the copy

# put copy of jcore.py where python3 can find it
# alternatively - set path to find it in J addons
#sys.path.append('/home/eric/j64-807/addons/api/python3'))

# requires j807 J Engine (JGetR new in 807)

# define full paths to J bin folder, shared library, and profile

# typical for linux/macos install in home (dylib instead of so for macos)
# pathbin= '/home/eric/j64-806/bin'
# pathdll= pathbin+'/libj.so'
# pathpro= pathbin+'/profile.ijs'

# typical for debian install
#pathbin= '/usr/bin'
#pathdll= '/usr/lib/x86_64-linux-gnu/libj.so'
#pathpro= '/etc/j/8.06/profile.ijs'

# typical for windows install in home
pathbin= 'c:/j64/j64-807/bin'
pathdll= pathbin+'/j.dll'
pathpro= pathbin+'/profile.ijs'

# perhaps add your enhancements here

#from jcore import * # get base python3->J routines
