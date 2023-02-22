echo off
title Running smug keyword update ...
pushd
setlocal

rem activate anaconda python
call c:\ProgramData\Anaconda3\Scripts\activate.bat 

rem Update local keyword changes files.
python updatesmugkeywords.py

title smug keyword update complete!
endlocal
popd
pause 