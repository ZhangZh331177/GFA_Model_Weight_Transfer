import os
InputDir = r"D:\GAMES\Modding\Python_MaxScript_Workdir\GFA_Model_Weight_Transfer\MaterialTools\set\breed"
OutputDir = r"D:\GAMES\Modding\Python_MaxScript_Workdir\GFA_Model_Weight_Transfer\MaterialTools\breed_patch"

SkinNameList =[
    "agf_aifu",
    "simon_zhouxue",
    "agf_anduosi", 
    "simon_yiweite",
    "agf_baxida", 
    "agf_biyouka", 
    "agf_bobosha", 
    "simon_tuoluoluo",
    "agf_chuntian",
    "simon_nijita", 
    "agf_daiyan", 
    "simon_buluoniyab",
    "agf_dushani", 
    "simon_buluoniyaa",
    "agf_fei", 
    "simon_zhouxue",
    "agf_feitusa", 
    "agf_fuluolun", 
    "simon_yiweite",
    "agf_habuxi", 
    "agf_hailun", 
    "agf_jiangyu", 
    "agf_kelukai", 
    "agf_keluolike", 
    "agf_kexieniya", 
    "simon_tuoluoluo",
    "agf_kouerfu", 
    "agf_laina", 
    "simon_nijita",
    "agf_laini", 
    "agf_laiya", 
    "simon_buluoniyab",
    "agf_linde", 
    "agf_litala", 
    "simon_buluoniyaa",
    "agf_liuyisi", 
    "agf_luobeila", 
    "agf_luoleilai", 
    "agf_luota", 
    "agf_maqiduo", 
    "agf_mishiti", 
    "agf_moxinnagan", 
    "agf_nagan", 
    "agf_nameixisi", 
    "agf_nijita", 
    "agf_peili", 
    "agf_peilitiya", 
    "agf_qiongjiu", 
    "agf_qita", 
    "agf_qiuhua", 
    "agf_saibulina", 
    "agf_sangduolaixi", 
    "agf_shandian", 
    "agf_suomi", 
    "agf_tuoluoluo", 
    "agf_weiketuo", 
    "agf_weimaxina", 
    "agf_weipulei", 
    "agf_wuerlide", 
    "agf_xiaan", 
    "agf_xiakeli", 
    "agf_yinghua", 
    "agf_youxi", 
    "agf_zhaohui", 
    "akq_aika", 
    "akq_aodaili", 
    "akq_fagelansi", 
    "akq_feisha", 
    "akq_fulaweiya", 
    "akq_jialadiya", 
    "akq_lawei", 
    "akq_leiouna", 
    "akq_madeleina", 
    "akq_meiruidisi", 
    "akq_ming", 
    "akq_mixueer", 
    "akq_qiandai", 
    "akq_xiangnaimei", 
    "akq_xinghui", 
    "akq_xinxia", 
    "akq_yiweite", 
]

CurrentSkinNameID = 0
for root, dirs, files in os.walk(InputDir):
    for fileName in files:
        if fileName.endswith(".set"):
            InputPath = os.path.join(root, fileName)
            InputRelPath = os.path.relpath(InputPath, InputDir)
            OutputPath = os.path.join(OutputDir,  InputRelPath)
            os.makedirs(os.path.dirname(OutputPath), exist_ok=True)
            
            UsingSkinName = SkinNameList[CurrentSkinNameID]
            CurrentSkinNameID += 1
            if CurrentSkinNameID >= len(SkinNameList):
                CurrentSkinNameID = 0

            with open(InputPath) as inputFile:
                with open(OutputPath, 'w') as outFile:
                    for line in inputFile:
                        if "{skin " in line:
                            line = line.split("{skin ")[0] + '{skin "' + UsingSkinName + '"}\n'
                        if "{portrait " in line:
                            line = line.split("{portrait ")[0] + '{portrait "' + UsingSkinName + '"}\n'
                        if "{nationality " in line:
                            line = line.split("{nationality ")[0] + '{nationality "' + UsingSkinName + '"}\n'
                        outFile.write(line)
