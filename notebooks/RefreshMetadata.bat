echo off
title Running refresh ALL metadata ...
pushd
setlocal

rem Refresh all album TAB delimited metadata files.
rem Assumes (smugpyter) is on python sys.path.
python refreshmetadata.py

title refresh ALL metadata complete!
endlocal
popd
pause