echo off
title Running refresh ALL metadata ...
pushd
setlocal

rem activate anaconda python
call c:\Anaconda3\Scripts\activate.bat 

rem Empty all CSV changes files in local directories.
rem Assumes (smugpyter) is on python sys.path.
python resetallchangesfiles.py

title refresh ALL metadata complete!
endlocal
popd
pause