echo off

rem compute print size keys for images in manifest files
rem and write changes CSV files. Changes files will only
rem have a header row if there are no keyword changes.
rem assumes (smugpyter, printkeys) is on python sys.path
python updateprintsizekeywords.py

pause 