import os
import subprocess

inputDir = r"D:\GAMES\Modding\Python_MaxScript_Workdir\GFA_Model_Weight_Transfer\MaterialTools\entity"
outputDir = r"D:\GAMES\Modding\Python_MaxScript_Workdir\GFA_Model_Weight_Transfer\MaterialTools\entity_patch"

for root, dirs, files in os.walk(inputDir):
    for file in files:
        if file.endswith(".dds"):
            InputPath = os.path.join(root, file)
            InputRelPath = os.path.relpath(InputPath, inputDir)
            OutputPath = os.path.join(outputDir, InputRelPath)
            os.makedirs(os.path.dirname(OutputPath), exist_ok=True)
            subprocess.check_output([r"C:\Program Files\NVIDIA Corporation\NVIDIA Texture Tools\nvtt_export.exe", "-o", f"{OutputPath}", "-f", "16", "-p", r"G:\SteamLibrary\steamapps\common\Call to Arms - Gates of Hell\BC1A_sRGBtoLinear.dpf", f'"{InputPath}"'])