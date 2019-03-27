echo off
title Running sample images update ...
pushd
setlocal

rem Download new sample images.
python updatesampleimages.py

endlocal
popd
pause 