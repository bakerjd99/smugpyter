echo off
title Running refresh RECENT metadata ...
pushd
setlocal

rem Refresh recent album TAB delimited metadata files.
rem Assumes (smugpyter) is on python sys.path.
python refreshrecentmetadata.py

title RECENT metadata complete!
endlocal
popd
pause