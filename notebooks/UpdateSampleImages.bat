echo off
title Running sample images update ...
pushd
setlocal

rem activate anaconda python
call c:\Anaconda3\Scripts\activate.bat 

rem Download new sample images.
python updatesampleimages.py

endlocal
popd
pause 