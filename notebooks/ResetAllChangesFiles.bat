echo off
title Running refresh ALL metadata ...
pushd
setlocal

rem Empty all CSV changes files in local directories.
rem Assumes (smugpyter) is on python sys.path.
python resetallchangesfiles.py

endlocal
popd
pause