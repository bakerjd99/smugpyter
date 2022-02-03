echo off
title Running refresh RECENT metadata ...
pushd
setlocal

rem activate anaconda python
call c:\Anaconda3\Scripts\activate.bat 

rem Refresh recent album TAB delimited metadata files.
python refreshrecentmetadata.py

title RECENT metadata complete!
endlocal
popd
pause