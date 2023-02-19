@echo off
echo "Starting to generate resources.py, please wait..."
pyrcc5 -o ../src/desktop/DyberPet/resources.py ../src/desktop/DyberPet/resources.qrc
echo "Successfully generated 1 file"
pause