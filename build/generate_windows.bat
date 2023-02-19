@echo off
echo "Starting to generate resources.py, please wait..."
pyrcc5 -o ../src/desktop/DyberPet/resources.py ../src/desktop/DyberPet/resources.qrc
echo "Successfully generated 1 file"
cd ../src/desktop/
pyinstaller -F -w run_DyberPet.py
copy .\dist\run_DyberPet.exe ..\..\output\DyberPet.exe
echo "Build complete, you can find file at the output folder."
echo "Starting cleaning folder..."
del /S /F /Q run_DyberPet.spec
del /S /F /Q .\build\*.*
del /S /F /Q .\dist\*.*
echo "Cleaning complete."
pause