import os
InputDir = r"D:\GAMES\Modding\Python_MaxScript_Workdir\GFA_Model_Weight_Transfer\MaterialTools\inventory"
OutputDir = r"D:\GAMES\Modding\Python_MaxScript_Workdir\GFA_Model_Weight_Transfer\MaterialTools\inventory_patch"

CurrentSkinNameID = 0
for root, dirs, files in os.walk(InputDir):
    for fileName in files:
        if fileName.endswith(".mdl"):
            InputPath = os.path.join(root, fileName)
            InputRelPath = os.path.relpath(InputPath, InputDir)
            OutputPath = os.path.join(OutputDir,  InputRelPath)
            os.makedirs(os.path.dirname(OutputPath), exist_ok=True)

            with open(InputPath) as inputFile:
                with open(OutputPath, 'w') as outFile:
                    for line in inputFile:
                        if "{VolumeView " in line and "}" in line:
                            line = ""
                        outFile.write(line)
