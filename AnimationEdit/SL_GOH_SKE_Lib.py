GOHParentDictForConstruction = {
    "BODY": "BASIS", 

    "FOOT1L": "BODY", 
    "FOOT2L": "FOOT1L", 
    "BONE06": "FOOT2L", 
    "FOOT3L": "FOOT2L", 
    "BONE07": "FOOT3L", 

    "FOOT1R": "BODY", 
    "FOOT2R": "FOOT1R", 
    "BONE03": "FOOT2R", 
    "FOOT3R": "FOOT2R", 
    "BONE05": "FOOT3R", 

    "IK_LEFTRIGHT": "BODY", 
    "IK_UPDOWN": "IK_LEFTRIGHT", 
    "HEAD": "IK_UPDOWN", 
    "VISOR": "HEAD", 

    "CLAVICLE_RIGHT": "IK_UPDOWN", 
    "HAND1R": "CLAVICLE_RIGHT", 
    "HAND2R": "HAND1R", 
    "HAND3R": "HAND2R", 
    "RIGHT_HAND": "HAND2R", 
    "HAND_ROT1R": "HAND2R", 
    "PALM1R": "HAND_ROT1R", 
    "PALM2R": "PALM1R", 
    "PALM3R": "PALM2R", 
    "PALM2R_HIDE": "PALM1R", 
    "PALM3R_HIDE": "PALM2R_HIDE", 
    "PALM4R_HIDE": "PALM3R_HIDE", 

    "CLAVICLE_LEFT": "IK_UPDOWN", 
    "HAND1L": "CLAVICLE_LEFT", 
    "HAND2L": "HAND1L", 
    "HAND3L": "HAND2L", 
    "LEFT_HAND": "HAND2L", 
    "HAND_ROT1L": "HAND2L", 
    "PALM1L": "HAND_ROT1L", 
    "PALM2L": "PALM1L", 
    "PALM3L": "PALM2L", 
    "PALM2L_HIDE": "PALM1L", 
    "PALM3L_HIDE": "PALM2L_HIDE", 
    "PALM4L_HIDE": "PALM3L_HIDE", 

    "IK CHAIN01": "BASIS", 
    "IK CHAIN02": "BASIS", 
    "IK CHAIN03": "BASIS", 
    "IK CHAIN04": "BASIS", 
    "IK CHAIN05": "BASIS", 
    "IK CHAIN06": "BASIS", 

    "PALM_IK_HOLDER_LEFT02": "BASIS", 
    "PALM_IK_HOLDER_LEFT01": "PALM_IK_HOLDER_LEFT02", 
    "PALM_IK_HOLDER_LEFT": "PALM_IK_HOLDER_LEFT01", 
    "IK CHAIN08": "PALM_IK_HOLDER_LEFT", 

    "PALM_IK_HOLDER_RIGHT02": "BASIS", 
    "PALM_IK_HOLDER_RIGHT01": "PALM_IK_HOLDER_RIGHT02", 
    "PALM_IK_HOLDER_RIGHT": "PALM_IK_HOLDER_RIGHT01", 
    "IK CHAIN07": "PALM_IK_HOLDER_RIGHT", 

    "PLACEMENT": "BODY", 

    "GUN_BACK": "IK_UPDOWN", 
    "FORESIGHT2ROT": "BASIS",
}

GOHParentDictForModification = {
    'BODY': 'BASIS', 

    'FOOT1L': 'BODY', 
    'FOOT2L': 'FOOT1L', 
    'BONE06': 'FOOT2L', 
    'FOOT3L': 'FOOT2L', 
    'BONE07': 'FOOT3L', 

    'FOOT1R': 'BODY', 
    'FOOT2R': 'FOOT1R', 
    'BONE03': 'FOOT2R', 
    'FOOT3R': 'FOOT2R', 
    'BONE05': 'FOOT3R', 

    'IK_LEFTRIGHT': 'BODY', 
    'IK_UPDOWN': 'IK_LEFTRIGHT', 
    'HEAD': 'IK_UPDOWN', 
    'VISOR': 'HEAD', 
    
    'CLAVICLE_RIGHT': 'IK_UPDOWN', 
    'HAND1R': 'CLAVICLE_RIGHT', 
    'HAND2R': 'HAND1R', 
    'HAND3R': 'HAND2R', 
    'RIGHT_HAND': 'HAND2R', 
    'HAND_ROT1R': 'HAND2R', 
    'PALM1R': 'HAND_ROT1R', 
    'PALM2R': 'PALM1R', 
    'PALM3R': 'PALM2R', 
    'PALM2R_HIDE': 'PALM1R', 
    'PALM3R_HIDE': 'PALM2R_HIDE', 
    'PALM4R_HIDE': 'PALM3R_HIDE', 

    'CLAVICLE_LEFT': 'IK_UPDOWN', 
    'HAND1L': 'CLAVICLE_LEFT', 
    'HAND2L': 'HAND1L', 
    'HAND3L': 'HAND2L', 
    'LEFT_HAND': 'HAND2L', 
    'HAND_ROT1L': 'HAND2L', 
    'PALM1L': 'HAND_ROT1L', 
    'PALM2L': 'PALM1L', 
    'PALM3L': 'PALM2L', 
    'PALM2L_HIDE': 'PALM1L', 
    'PALM3L_HIDE': 'PALM2L_HIDE', 
    'PALM4L_HIDE': 'PALM3L_HIDE', 

    'IK CHAIN01': 'FOOT3R', 
    'IK CHAIN02': 'FOOT3R', 
    'IK CHAIN03': 'FOOT3L', 
    'IK CHAIN04': 'FOOT3L', 
    'IK CHAIN05': 'HAND3R', 
    'IK CHAIN06': 'HAND3L', 

    'PALM_IK_HOLDER_LEFT02': 'HAND2L', 
    'PALM_IK_HOLDER_LEFT01': 'HAND3L',
    'PALM_IK_HOLDER_LEFT':  'HAND3L',
    'IK CHAIN08':  'HAND3L',

    'PALM_IK_HOLDER_RIGHT02': 'HAND2R', 
    'PALM_IK_HOLDER_RIGHT01': 'HAND3R',
    'PALM_IK_HOLDER_RIGHT': 'HAND3R',
    'IK CHAIN07': 'HAND3R',
    
    'PLACEMENT': 'BODY', 

    'GUN_BACK': 'IK_UPDOWN', 
    'FORESIGHT2ROT': 'BASIS', 
}

def IsParentInGOHModificationSke(BoneNameChild, BoneNameParent):
    CurrentBone = BoneNameChild.upper()
    TargetName = BoneNameParent.upper()
    while CurrentBone in GOHParentDictForModification:
        CurrentBone = GOHParentDictForModification[CurrentBone]
        if CurrentBone == TargetName:
            return True
    return False

def GetDirectChidsOfListInConstructionSke(AllBoneNames, ParentBoneNames):
    ChildList = list()
    ParentBoneNamesUpper = [ParentBoneName.upper() for ParentBoneName in ParentBoneNames]
    for NodeName in AllBoneNames:
        NodeNameUpper = NodeName.upper()
        if NodeNameUpper in GOHParentDictForConstruction.keys():
            if GOHParentDictForConstruction[NodeNameUpper] in ParentBoneNamesUpper:
                ChildList.append(NodeNameUpper)
    return ChildList