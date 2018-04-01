# routines to access J from python3 - used by jbase.py

from jbase import pathbin,pathdll,pathpro
from ctypes import *
import numpy as np

jt= 0

def tob(s):
 if type(s) is str:
  s= s.encode('utf-8')
 return s

def init(loadprofile=True):
 global libj,jt
 if jt!=0:
  raise AssertionError('J: init already run')
 libj=  CDLL(pathdll)
 libj.JInit.restype = c_void_p
 libj.JGetR.restype = c_char_p
 jt= libj.JInit()
 if jt==0:
  raise AsserttionError('J: init library failed')
 if loadprofile:
  if 0!=do("0!:0<'"+pathpro+"'[BINPATH_z_=:'"+pathbin+"'[ARGV_z_=:''"):
   raise AssertionError('J: load profile failed')

def do(a): # run sentence and return error code
 return libj.JDo(c_void_p(jt),tob(a))

def dor(a): # run sentence and print output result
 libj.JDo(c_void_p(jt),tob(a))
 s= getr()[:-1]
 if 0!=len(s):
  print(s)

def getr(): # get output result from last sentence
 return string_at(libj.JGetR(c_void_p(jt))).decode('utf-8')

def get(n): # get value of J noun
 dt= c_longlong(0) ; dr= c_longlong(0) ; ds= c_longlong(0) ; dd= c_longlong(0)
 e= libj.JGetM(c_void_p(jt),tob(n),byref(dt),byref(dr),byref(ds),byref(dd))
 t= dt.value
 if t==0: # e not set for error
  raise AssertionError('J: get arg not a name')
 shape= np.fromstring(string_at(ds.value,dr.value*8),dtype=np.int64)
 count= np.prod(shape)
 if t==2:
  r= (string_at(dd.value,count)) #.decode("utf-8")
 elif t==4:
  r= np.fromstring(string_at(dd.value,count*8),dtype=np.int64)
  r.shape= shape
 elif t==8:
  r= np.fromstring(string_at(dd.value,count*8),dtype=np.float64)
  r.shape= shape
 else:
  raise AssertionError('J: get type not supported')
 return r

def set(n,d): # set J noun with value
 n= tob(n) ; d= tob(d)
 dt= c_longlong(0) 
 if type(d) is bytes:
  dt.value= 2
  dr= c_longlong(1)
  ds= c_longlong(len(d))
  ss= c_char_p(string_at(addressof(ds),8))
  dd= c_char_p(d)
 else:
  dt.value= 4 if d.dtype=='int64' else 8
  p= np.asarray(d.shape,c_longlong)
  dr= c_longlong(len(p))
  ss= c_char_p(p.tobytes())
  dd= c_char_p(d.tobytes())
 e= libj.JSetM(c_void_p(jt),n,byref(dt),byref(dr), byref(ss) ,byref(dd))
 if e!=0:
  raise AssertionError('J: set arg not a name')

def j(): # run J sentences until ....
 while 1:
  s= input('   ')
  if s == '....':
   break
  dor(s)

def test(): # validation
 do('a=: i.2 3') ; a= get('a') ; set('b',23+a) ; b= get('b') ; print(b) ; print('.... to exit') ; j()
 