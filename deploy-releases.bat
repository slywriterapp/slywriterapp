@echo off
REM Deploy script for two-repo setup
REM Builds from private repo, publishes to public repo

echo Building SlyWriter...
cd slywriter-electron
call npm run dist:squirrel

echo Copying to releases repo...
copy dist\*.exe ..\slywriter-releases\
copy dist\*.nupkg ..\slywriter-releases\
copy dist\RELEASES ..\slywriter-releases\

echo Publishing to public releases repo...
cd ..\slywriter-releases
git add .
git commit -m "Release v%1"
git tag v%1
git push origin main --tags

echo Creating GitHub Release...
gh release create v%1 *.exe *.nupkg RELEASES --title "SlyWriter v%1" --notes "Update release"

echo Done! Updates will be available from public repo.