echo off
title Running smug keyword update ...
pushd
setlocal

rem Update local keyword changes files.
python updatesmugkeywords.py

title smug keyword update complete!
endlocal
popd
pause 