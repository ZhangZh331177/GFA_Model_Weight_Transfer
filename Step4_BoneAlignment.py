import math
from pymxs import runtime as rt

def GetNodeByNameRaiser(InputNodeName):
    TargetNode = rt.getNodeByName(InputNodeName)
    if TargetNode == None:
        raise ValueError("Trying to GetNodeByName on an Unknown Name: [" + InputNodeName + "]!")
    else:
        return TargetNode

def GetPosFromNodeName(InputNodeName):
    return GetNodeByNameRaiser(InputNodeName).pos

def GetMeanPoseFromNodeNameList(InputNodeNameList):
    NodePosList = list()
    for NodeName in InputNodeNameList:
        NodePosList.append(GetPosFromNodeName(NodeName))
    return sum(NodePosList) / len(NodePosList)

def GetProjectedRotationOfPos(Pos1, Pos2, Plane):
    # This function is not designed to get precise rotation.
    # It is used to generate nearest rotation only to align the projection in specific axis
    DirectonVec = Pos2 - Pos1
    if Plane == "XY":
        return -math.degrees(math.atan2(DirectonVec.x, DirectonVec.u))
        # return math.degrees(math.asin(DirectonVec.y / ((DirectonVec.x**2 + DirectonVec.y **2) ** 0.5)))
    elif Plane == "YZ":
        return -math.degrees(math.atan2(DirectonVec.y, DirectonVec.z))
        # return math.degrees(math.asin(DirectonVec.y / ((DirectonVec.y**2 + DirectonVec.z **2) ** 0.5)))
    elif Plane == "XZ":
        return -math.degrees(math.atan2(DirectonVec.x, DirectonVec.z))
        # return math.degrees(math.asin(DirectonVec.x / ((DirectonVec.x**2 + DirectonVec.z **2) ** 0.5)))
    else:
        raise ValueError("Plane should be one of 'XY', 'YZ' or 'XZ', Input value is "+Plane+"!")


def GetProjectedRotation(Object1, Object2, Plane):
    # This function is not designed to get precise rotation.
    # It is used to generate nearest rotation only to align the projection in specific axis
    return GetProjectedRotationOfPos(Object2.pos, Object1.pos, Plane)

def GetVectorLength(MaxVector):
    return ((MaxVector.x **2) + (MaxVector.y **2) + (MaxVector.z **2)) ** 0.5

def ApplyRotationOnPlane(TargetBone, Angle, Plane):
    if Plane == "XY":
        rt.rotate(TargetBone, rt.eulerangles(0, 0, Angle))
    elif Plane == "YZ":
        rt.rotate(TargetBone, rt.eulerangles(Angle, 0, 0))
    elif Plane == "XZ":
        rt.rotate(TargetBone, rt.eulerangles(0, Angle, 0))
    else:
        raise ValueError("Plane should be one of 'XY', 'YZ' or 'XZ', Input value is '"+Plane+"'!")


def AlignBoneRotationOnPlane(RotatingBone, TargetBone, Plane):
    # Make two bones's projection on target plane parallel.
    
    # Get Rotation difference
    RotatingBoneStart = GetNodeByNameRaiser(RotatingBone[0])
    RotatingBoneEnd = GetNodeByNameRaiser(RotatingBone[1])
    RotatingBoneProjectedRotation = GetProjectedRotation(RotatingBoneStart, RotatingBoneEnd, Plane)
    print(RotatingBoneProjectedRotation)

    TargetBoneStart = GetNodeByNameRaiser(TargetBone[0])
    TargetBoneEnd = GetNodeByNameRaiser(TargetBone[1])
    TargetBoneProjectedRotation = GetProjectedRotation(TargetBoneStart, TargetBoneEnd, Plane)
    print(TargetBoneProjectedRotation)

    RotationDiff = TargetBoneProjectedRotation - RotatingBoneProjectedRotation
    # Apply Rotation
    ApplyRotationOnPlane(RotatingBoneStart, RotationDiff, Plane)

def AlignBoneLength(ScalingBone, TargetBone, MainLocalAxis, UseProjectionLength = False):
    # Make two bones's Length Identical by Scaling the bone.
    OtherAxisScaleFactor = 0.5

    # Get Length Difference
    ScalingBoneStart = GetNodeByNameRaiser(ScalingBone[0])
    ScalingBoneEnd = GetNodeByNameRaiser(ScalingBone[1])
    ScalingBoneVector = ScalingBoneEnd.pos - ScalingBoneStart.pos

    TargetBoneStart = GetNodeByNameRaiser(TargetBone[0])
    TargetBoneEnd = GetNodeByNameRaiser(TargetBone[1])
    TargetBoneVector = TargetBoneEnd.pos - TargetBoneStart.pos
    
    if UseProjectionLength:
        raise NotImplementedError("Scaling with projection length is not implemented!")
    else:
        LengthRatio = GetVectorLength(TargetBoneVector) / GetVectorLength(ScalingBoneVector)
    
    # Apply Scaling
    CurrentScale = ScalingBoneStart.scale
    if MainLocalAxis == "X":
        CurrentScale.x *= LengthRatio
        CurrentScale.y *= (LengthRatio ** OtherAxisScaleFactor)
        CurrentScale.z *= (LengthRatio ** OtherAxisScaleFactor)
    elif MainLocalAxis == "Y":
        CurrentScale.x *= (LengthRatio ** OtherAxisScaleFactor)
        CurrentScale.y *= LengthRatio
        CurrentScale.z *= (LengthRatio ** OtherAxisScaleFactor)
    elif MainLocalAxis == "Z":
        CurrentScale.x *= (LengthRatio ** OtherAxisScaleFactor)
        CurrentScale.y *= (LengthRatio ** OtherAxisScaleFactor)
        CurrentScale.z *= LengthRatio
    else:
        raise ValueError("MainLocalAxis should be one of 'X', 'Y' or 'Z', Input value is '"+MainLocalAxis+"'!")
    ScalingBoneStart.scale = CurrentScale

def NormalizeScale(InputBoneName):
    # Rescale the input bone to restore 1:1:1 scaling, use geometric mean
    InputBone = GetNodeByNameRaiser(InputBoneName)
    InputBoneParent = InputBone.parent
    InputBone.parent = None
    CurrentScale = InputBone.scale
    MeanScale = abs(CurrentScale.x * CurrentScale.y * CurrentScale.z) ** (1.0 / 3.0)
    if CurrentScale.x > 0:
        CurrentScale.x = MeanScale
    else:
        CurrentScale.x = -MeanScale

    if CurrentScale.y > 0:
        CurrentScale.y = MeanScale
    else:
        CurrentScale.y = -MeanScale

    if CurrentScale.z > 0:
        CurrentScale.z = MeanScale
    else:
        CurrentScale.z = -MeanScale
    InputBone.scale = CurrentScale
    InputBone.parent = InputBoneParent

def GetProjectionLength(Pos1, Pos2):
    DotProduct = (Pos1.x * Pos2.x) + (Pos1.y * Pos2.y) + (Pos1.z * Pos2.z)
    MagnitudePosB = ((Pos2.x ** 2) + (Pos2.y ** 2) + (Pos2.z ** 2)) ** 0.5
    
    if MagnitudePosB == 0:
        raise ValueError("vector_b cannot be a zero vector")
    
    return DotProduct / MagnitudePosB


# We assume that both models are facing X+ (Right), and Head up to Z+ (UP), with foot contact the ground (Z=0)


# Parameter
MMD_RootName = "GirlsFrontline AlvaDefault"
MMD_Root = GetNodeByNameRaiser(MMD_RootName)

# These Names SHOULD be fixed in different run

## Lower Body Alignment

### UpperLeg
GOH_UpperLegLeft = ("GFA_MWT_SKE_foot1L", "GFA_MWT_SKE_foot2L")
GOH_UpperLegRight = ("GFA_MWT_SKE_foot1R", "GFA_MWT_SKE_foot2R")

MMD_UpperLegLeft = ("Leg_L", "Knee_L")
MMD_UpperLegRight = ("Leg_R", "Knee_R")
MMD_UpperLegDLeft = ("LegD_L", "KneeD_L") # Why is there a "D" postfixed version?
MMD_UpperLegDRight = ("LegD_R", "KneeD_R") # Why is there a "D" postfixed version?

UpperLegScalingAxis = "Y"

## UpperLeg: Scaling Y -> Rotation YZ -> Rotation XZ
## UpperLeg Scaling
AlignBoneLength(MMD_UpperLegLeft, GOH_UpperLegLeft, UpperLegScalingAxis)
AlignBoneLength(MMD_UpperLegRight, GOH_UpperLegRight, UpperLegScalingAxis)
AlignBoneLength(MMD_UpperLegDLeft, GOH_UpperLegLeft, UpperLegScalingAxis)
AlignBoneLength(MMD_UpperLegDRight, GOH_UpperLegRight, UpperLegScalingAxis)

## UpperLeg Rotation (YZ -> XZ)
AlignBoneRotationOnPlane(MMD_UpperLegLeft, GOH_UpperLegLeft, "YZ")
AlignBoneRotationOnPlane(MMD_UpperLegLeft, GOH_UpperLegLeft, "XZ")

AlignBoneRotationOnPlane(MMD_UpperLegRight, GOH_UpperLegRight, "YZ")
AlignBoneRotationOnPlane(MMD_UpperLegRight, GOH_UpperLegRight, "XZ")

AlignBoneRotationOnPlane(MMD_UpperLegDLeft, GOH_UpperLegLeft, "YZ")
AlignBoneRotationOnPlane(MMD_UpperLegDLeft, GOH_UpperLegLeft, "XZ")

AlignBoneRotationOnPlane(MMD_UpperLegDRight, GOH_UpperLegRight, "YZ")
AlignBoneRotationOnPlane(MMD_UpperLegDRight, GOH_UpperLegRight, "XZ")

### LowerLeg
GOH_LowerLegLeft = ("GFA_MWT_SKE_foot2L", "GFA_MWT_SKE_foot3L")
GOH_LowerLegRight = ("GFA_MWT_SKE_foot2R", "GFA_MWT_SKE_foot3R")

MMD_LowerLegLeft = ("Knee_L", "Ankle_L")
MMD_LowerLegRight = ("Knee_R", "Ankle_R")
MMD_LowerLegDLeft = ("KneeD_L", "AnkleD_L") # Why is there a "D" postfixed version?
MMD_LowerLegDRight = ("KneeD_R", "AnkleD_R") # Why is there a "D" postfixed version?

LowerLegScalingAxis = "Y"

## LowerLeg: Scaling Y -> Rotation YZ -> Rotation XZ
## LowerLeg Scaling
AlignBoneLength(MMD_LowerLegLeft, GOH_LowerLegLeft, LowerLegScalingAxis)
AlignBoneLength(MMD_LowerLegRight, GOH_LowerLegRight, LowerLegScalingAxis)
AlignBoneLength(MMD_LowerLegDLeft, GOH_LowerLegLeft, LowerLegScalingAxis)
AlignBoneLength(MMD_LowerLegDRight, GOH_LowerLegRight, LowerLegScalingAxis)

## LowerLeg Rotation (YZ -> XZ)
AlignBoneRotationOnPlane(MMD_LowerLegLeft, GOH_LowerLegLeft, "YZ")
AlignBoneRotationOnPlane(MMD_LowerLegLeft, GOH_LowerLegLeft, "XZ")

AlignBoneRotationOnPlane(MMD_LowerLegRight, GOH_LowerLegRight, "YZ")
AlignBoneRotationOnPlane(MMD_LowerLegRight, GOH_LowerLegRight, "XZ")

AlignBoneRotationOnPlane(MMD_LowerLegDLeft, GOH_LowerLegLeft, "YZ")
AlignBoneRotationOnPlane(MMD_LowerLegDLeft, GOH_LowerLegLeft, "XZ")

AlignBoneRotationOnPlane(MMD_LowerLegDRight, GOH_LowerLegRight, "YZ")
AlignBoneRotationOnPlane(MMD_LowerLegDRight, GOH_LowerLegRight, "XZ")

## Normalize Foot Scale
NormalizeScale(MMD_LowerLegLeft[1])
NormalizeScale(MMD_LowerLegRight[1])
NormalizeScale(MMD_LowerLegDLeft[1])
NormalizeScale(MMD_LowerLegDRight[1])


# Upper Body Alignment (Upper body alignment is complex, so we split it up)

## Pre-Alignment: Use Root Rotation to Align the direction, and realign the UpperLegs
GOH_UpperBodySourceList = ["GFA_MWT_SKE_foot1L", "GFA_MWT_SKE_foot1R"]
GOH_UpperBodyTargetList = ["GFA_MWT_SKE_Clavicle_left", "GFA_MWT_SKE_Clavicle_right"]
MMD_UpperBodySourceList = ["Leg_L", "Leg_R"]
MMD_UpperBodySourceDList = ["LegD_L", "LegD_R"]
MMD_UpperBodyTargetList = ["ShoulderP_L", "ShoulderP_R"]

UpperBodyAlignmentPlane = "XZ"

GOH_UpperBodySourcePos = GetMeanPoseFromNodeNameList(GOH_UpperBodySourceList)
GOH_UpperBodyTargetPos = GetMeanPoseFromNodeNameList(GOH_UpperBodyTargetList)
GOH_UpperBodyDirection = GetProjectedRotationOfPos(GOH_UpperBodySourcePos, GOH_UpperBodyTargetPos, UpperBodyAlignmentPlane)

MMD_UpperBodySourcePos = GetMeanPoseFromNodeNameList(MMD_UpperBodySourceList)
MMD_UpperBodyTargetPos = GetMeanPoseFromNodeNameList(MMD_UpperBodyTargetList)
MMD_UpperBodyDirection = GetProjectedRotationOfPos(MMD_UpperBodySourcePos, MMD_UpperBodyTargetPos, UpperBodyAlignmentPlane)

UpperBodyDirectionDiff = GOH_UpperBodyDirection - MMD_UpperBodyDirection

### Rotate Root Bone
ApplyRotationOnPlane(MMD_Root, UpperBodyDirectionDiff, UpperBodyAlignmentPlane)
### Move Root Bone to Re-Align Legs
MMD_Root.pos = MMD_Root.pos + (MMD_UpperBodySourcePos - GetMeanPoseFromNodeNameList(MMD_UpperBodySourceList))
### Rotate legs to Re-Align
for BoneName in MMD_UpperBodySourceList + MMD_UpperBodySourceDList:
    ApplyRotationOnPlane(GetNodeByNameRaiser(BoneName), -UpperBodyDirectionDiff, UpperBodyAlignmentPlane)

## Distribute rotation and position to the chain

### Get each Step of upper body
MMD_UpperBodyChain = [
    MMD_UpperBodySourceList,
    ["UpperBody"],
    ["UpperBody2"],
    MMD_UpperBodyTargetList
]
MMD_NeckBoneName = "Neck"
GOH_NeckBoneName = "GFA_MWT_SKE_Head"
UpperBodyOverAllVector = GetMeanPoseFromNodeNameList(MMD_UpperBodyChain[-1]) - GetMeanPoseFromNodeNameList(MMD_UpperBodyChain[0])
UpperBodySteps = list()
TotalWeight = 0
for i in range(1, len(MMD_UpperBodyChain)):
    CurrentStepStartPos = GetMeanPoseFromNodeNameList(MMD_UpperBodyChain[i-1])
    CurrentStepEndPos = GetMeanPoseFromNodeNameList(MMD_UpperBodyChain[i])
    CurrentStepStartBones = list()
    CurrentStepEndBones = list()
    for BoneName in MMD_UpperBodyChain[i-1]:
        CurrentStepStartBones.append(GetNodeByNameRaiser(BoneName))
    for BoneName in MMD_UpperBodyChain[i]:
        CurrentStepEndBones.append(GetNodeByNameRaiser(BoneName))
    CurrentStepVector = CurrentStepEndPos - CurrentStepStartPos
    CurrentStepWeightRaw = GetProjectionLength(CurrentStepVector, UpperBodyOverAllVector)

    UpperBodySteps.append([CurrentStepStartBones, CurrentStepEndBones, CurrentStepWeightRaw])
    TotalWeight += CurrentStepWeightRaw

### Distribute Backward rotation
for CurrentStepStartBones, CurrentStepEndBones, CurrentStepWeightRaw in UpperBodySteps:
    CurrentStepWeight = CurrentStepWeightRaw / TotalWeight
    for CurrentBone in CurrentStepEndBones:
        ApplyRotationOnPlane(CurrentBone, -(UpperBodyDirectionDiff * CurrentStepWeight), UpperBodyAlignmentPlane)

#### Also BackRotate the neck with the shoulder
ShoulderWeight = UpperBodySteps[-1][-1] / TotalWeight
ApplyRotationOnPlane(GetNodeByNameRaiser(MMD_NeckBoneName), -(UpperBodyDirectionDiff * ShoulderWeight), UpperBodyAlignmentPlane)

### Distribute scaling
#### Recacluate the Scale needed
GOH_UpperBodySourcePos = GetMeanPoseFromNodeNameList(GOH_UpperBodySourceList)
GOH_UpperBodyTargetPos = GetMeanPoseFromNodeNameList(GOH_UpperBodyTargetList)

MMD_UpperBodySourcePos = GetMeanPoseFromNodeNameList(MMD_UpperBodySourceList)
MMD_UpperBodyTargetPos = GetMeanPoseFromNodeNameList(MMD_UpperBodyTargetList)

LengthScaleNeeded = GetVectorLength(GOH_UpperBodyTargetPos - GOH_UpperBodySourcePos) / GetVectorLength(MMD_UpperBodyTargetPos - MMD_UpperBodySourcePos)

CumulativeShoulderScale = 1.0 # We record this value for further hip scaling
for CurrentStepStartBones, CurrentStepEndBones, CurrentStepWeightRaw in UpperBodySteps[1:]: # MMD_UpperBodySourceList (Legs) DO NOT SCALE, so we used [1:]!
    CurrentStepScaling = LengthScaleNeeded ** (CurrentStepWeightRaw / TotalWeight)
    for CurrentBone in CurrentStepStartBones:
        CurrentScale = CurrentBone.scale
        CurrentScale.x = CurrentScale.x * (CurrentStepScaling ** 0.5)
        CurrentScale.y = CurrentScale.y * CurrentStepScaling
        CurrentScale.z = CurrentScale.z * (CurrentStepScaling ** 0.5)
        CumulativeShoulderScale *= (CurrentStepScaling ** 0.5)
        CurrentBone.scale = CurrentScale

#### Normalize shoulder scale
for CurrentBone in UpperBodySteps[-1][1]: # Last step end bones
    NormalizeScale(CurrentBone.name)
#### Also Normalize the neck 
NormalizeScale(MMD_NeckBoneName)

### Distribute offset
GOH_UpperBodyTargetList_With_Neck = GOH_UpperBodyTargetList + [GOH_NeckBoneName]
MMD_UpperBodyTargetList_With_Neck = MMD_UpperBodyTargetList + [MMD_NeckBoneName]
UpperBodyWithNeckOffsetCollected = GetMeanPoseFromNodeNameList(GOH_UpperBodyTargetList_With_Neck) - GetMeanPoseFromNodeNameList(MMD_UpperBodyTargetList_With_Neck)

for CurrentStepStartBones, CurrentStepEndBones, CurrentStepWeightRaw in UpperBodySteps:
    CurrentStepWeight = CurrentStepWeightRaw / TotalWeight
    for CurrentBone in CurrentStepStartBones:
        CurrentBone.pos = CurrentBone.pos + (UpperBodyWithNeckOffsetCollected * CurrentStepWeight)

### Apply Final offset
UpperBodyOffsetCollected = GetMeanPoseFromNodeNameList(GOH_UpperBodyTargetList) - GetMeanPoseFromNodeNameList(MMD_UpperBodyTargetList)
for CurrentBoneName in MMD_UpperBodyTargetList:
    CurrentBone = GetNodeByNameRaiser(CurrentBoneName)
    CurrentBone.pos = CurrentBone.pos + UpperBodyOffsetCollected
#### Also Apply to neck
GetNodeByNameRaiser(MMD_NeckBoneName).pos = GetNodeByNameRaiser(GOH_NeckBoneName).pos