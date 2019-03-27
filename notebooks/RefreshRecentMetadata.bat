echo off
title Running refresh RECENT metadata ...
pushd
setlocal

rem Refresh recent album TAB delimited metadata files.
rem Assumes (smugpyter) is on python sys.path.
python refreshrecentmetadata.py

endlocal
popd
pause