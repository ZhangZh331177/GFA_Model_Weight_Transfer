import math
import pymxs
from pymxs import runtime as rt

def SolveResizeChainRatio(WeightList, TargetResizeRatio, IterationTimes, low, high):
    WS = sum(WeightList)
    
    cumulative_product = [WeightList[0]]
    for i in range(1, len(WeightList)):
        cumulative_product.append(cumulative_product[-1] * WeightList[i])
    
    def f(N):
        result = 0.0
        for i, (W, C) in enumerate(zip(WeightList, cumulative_product)):
            result += (W * C) * (N ** (i + 1.0))
        return result - (TargetResizeRatio * WS)
    
    f_low = f(low)
    f_high = f(high)
    
    if f_low == 0:
        return low
    if f_high == 0:
        return high
    
    for i in range(IterationTimes):
        mid = (low + high) / 2.0
        f_mid = f(mid)
        
        if f_mid == 0.0:
            return mid
        
        if f_low * f_mid <= 0.0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid
    
    return (low + high) / 2.0

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
        angle = math.degrees(math.atan2(DirectonVec.y, DirectonVec.x))
    elif Plane == "YZ":
        angle = math.degrees(math.atan2(DirectonVec.z, DirectonVec.y))
    elif Plane == "XZ":
        angle = math.degrees(math.atan2(DirectonVec.z, DirectonVec.x))
    else:
        raise ValueError("Plane should be one of 'XY', 'YZ' or 'XZ', Input value is "+Plane+"!")
    
    if angle < 0:
        angle += 360
    
    return angle

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
        rt.rotate(TargetBone, rt.eulerangles(0, -Angle, 0))
    else:
        raise ValueError("Plane should be one of 'XY', 'YZ' or 'XZ', Input value is '"+Plane+"'!")

def ApplyRotationOnLocalAxis(TargetBone, Angle, Axis):
    coordsys = getattr(pymxs.runtime, '%coordsys_context')
    prev_coordsys = coordsys(pymxs.runtime.Name('local'), None)

    if Axis == "X":
        rt.rotate(TargetBone, rt.eulerangles(Angle, 0, 0))
    elif Axis == "Y":
        rt.rotate(TargetBone, rt.eulerangles(0, Angle, 0))
    elif Axis == "Z":
        rt.rotate(TargetBone, rt.eulerangles(0, 0, Angle))
    else:
        coordsys(prev_coordsys, None)
        raise ValueError("Axis should be one of 'X', 'Y' or 'Z', Input value is '"+Axis+"'!")
    coordsys(prev_coordsys, None)

def ApplyRotationOnLocalAxisByName(TargetBoneName, Angle, Axis):
    ApplyRotationOnLocalAxis(GetNodeByNameRaiser(TargetBoneName), Angle, Axis)

def AlignBoneRotationOnPlane(RotatingBone, TargetBone, Plane):
    # Make two bones's projection on target plane parallel.
    
    # Get Rotation difference
    RotatingBoneStart = GetNodeByNameRaiser(RotatingBone[0])
    RotatingBoneEnd = GetNodeByNameRaiser(RotatingBone[1])
    RotatingBoneProjectedRotation = GetProjectedRotation(RotatingBoneStart, RotatingBoneEnd, Plane)

    TargetBoneStart = GetNodeByNameRaiser(TargetBone[0])
    TargetBoneEnd = GetNodeByNameRaiser(TargetBone[1])
    TargetBoneProjectedRotation = GetProjectedRotation(TargetBoneStart, TargetBoneEnd, Plane)

    RotationDiff = TargetBoneProjectedRotation - RotatingBoneProjectedRotation
    # Apply Rotation
    ApplyRotationOnPlane(RotatingBoneStart, RotationDiff, Plane)

def AlignBoneLength(ScalingBone, TargetBone, MainLocalAxis, UseProjectionLength = False, LengthRatioToTarget = 1.0, OtherAxisScaleFactor = 0.5):
    # Make two bones's Length Identical by Scaling the bone.
    try:
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
            LengthRatio = (GetVectorLength(TargetBoneVector) / GetVectorLength(ScalingBoneVector)) * LengthRatioToTarget
        
        # Apply Scaling
        ## Use local coords to scale
        coordsys = getattr(pymxs.runtime, '%coordsys_context')
        prev_coordsys = coordsys(pymxs.runtime.Name('local'), None)

        MainScale = LengthRatio
        OtherScale = LengthRatio ** OtherAxisScaleFactor
        # CurrentScale = ScalingBoneStart.scale
        if MainLocalAxis == "X":
            rt.scale(ScalingBoneStart, rt.Point3(MainScale,OtherScale,OtherScale))
        elif MainLocalAxis == "Y":
            rt.scale(ScalingBoneStart, rt.Point3(OtherScale,MainScale,OtherScale))
        elif MainLocalAxis == "Z":
            rt.scale(ScalingBoneStart, rt.Point3(OtherScale,OtherScale,MainScale))
        else:
            raise ValueError("MainLocalAxis should be one of 'X', 'Y' or 'Z', Input value is '"+MainLocalAxis+"'!")
        

        # Restore previous coord
        coordsys(prev_coordsys, None)
    except Exception as e:
        Bone_A_Str = "'" + ScalingBone[0] + "','" + ScalingBone[1] + "'"
        Bone_B_Str = "'" + TargetBone[0] + "','" + TargetBone[1] + "'"
        raise RuntimeError("AlignBoneLength Raised Error: Failed to align Bone ["+Bone_A_Str+"] to Bone ["+Bone_B_Str+"] due to following exception:" + str(e))


def NormalizeScale(InputBoneName):
    # Rescale the input bone to restore 1:1:1 scaling, use geometric mean
    ## Break The relationship
    InputBone = GetNodeByNameRaiser(InputBoneName)
    InputBoneParent = InputBone.parent
    InputBone.parent = None

    # Scale
    CurrentScale = InputBone.scale
    MeanScale = abs(CurrentScale.x * CurrentScale.y * CurrentScale.z) ** (1.0 / 3.0)
    if CurrentScale.x > 0:
        NewScaleX = MeanScale
    else:
        NewScaleX = -MeanScale

    if CurrentScale.y > 0:
        NewScaleY = MeanScale
    else:
        NewScaleY = -MeanScale

    if CurrentScale.z > 0:
        NewScaleZ = MeanScale
    else:
        NewScaleZ = -MeanScale
    InputBone.scale = rt.Point3(NewScaleX, NewScaleY, NewScaleZ)
    
    # Restore relationship
    InputBone.parent = InputBoneParent

def NormalizeScaleBreakLink(InputBoneName):
    # Rescale the input bone to restore 1:1:1 scaling, use geometric mean
    ## Break The relationship
    InputBone = GetNodeByNameRaiser(InputBoneName)
    InputBoneParent = InputBone.parent
    InputBone.parent = None

    # Scale
    CurrentScale = InputBone.scale
    MeanScale = abs(CurrentScale.x * CurrentScale.y * CurrentScale.z) ** (1.0 / 3.0)
    if CurrentScale.x > 0:
        NewScaleX = MeanScale
    else:
        NewScaleX = -MeanScale

    if CurrentScale.y > 0:
        NewScaleY = MeanScale
    else:
        NewScaleY = -MeanScale

    if CurrentScale.z > 0:
        NewScaleZ = MeanScale
    else:
        NewScaleZ = -MeanScale
    InputBone.scale = rt.Point3(NewScaleX, NewScaleY, NewScaleZ)


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
AlignBoneRotationOnPlane(MMD_UpperLegLeft, GOH_UpperLegLeft, "YZ")
AlignBoneRotationOnPlane(MMD_UpperLegLeft, GOH_UpperLegLeft, "XZ")

AlignBoneRotationOnPlane(MMD_UpperLegRight, GOH_UpperLegRight, "YZ")
AlignBoneRotationOnPlane(MMD_UpperLegRight, GOH_UpperLegRight, "XZ")
AlignBoneRotationOnPlane(MMD_UpperLegRight, GOH_UpperLegRight, "YZ")
AlignBoneRotationOnPlane(MMD_UpperLegRight, GOH_UpperLegRight, "XZ")

AlignBoneRotationOnPlane(MMD_UpperLegDLeft, GOH_UpperLegLeft, "YZ")
AlignBoneRotationOnPlane(MMD_UpperLegDLeft, GOH_UpperLegLeft, "XZ")
AlignBoneRotationOnPlane(MMD_UpperLegDLeft, GOH_UpperLegLeft, "YZ")
AlignBoneRotationOnPlane(MMD_UpperLegDLeft, GOH_UpperLegLeft, "XZ")

AlignBoneRotationOnPlane(MMD_UpperLegDRight, GOH_UpperLegRight, "YZ")
AlignBoneRotationOnPlane(MMD_UpperLegDRight, GOH_UpperLegRight, "XZ")
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
AlignBoneRotationOnPlane(MMD_LowerLegLeft, GOH_LowerLegLeft, "YZ")
AlignBoneRotationOnPlane(MMD_LowerLegLeft, GOH_LowerLegLeft, "XZ")

AlignBoneRotationOnPlane(MMD_LowerLegRight, GOH_LowerLegRight, "YZ")
AlignBoneRotationOnPlane(MMD_LowerLegRight, GOH_LowerLegRight, "XZ")
AlignBoneRotationOnPlane(MMD_LowerLegRight, GOH_LowerLegRight, "YZ")
AlignBoneRotationOnPlane(MMD_LowerLegRight, GOH_LowerLegRight, "XZ")

AlignBoneRotationOnPlane(MMD_LowerLegDLeft, GOH_LowerLegLeft, "YZ")
AlignBoneRotationOnPlane(MMD_LowerLegDLeft, GOH_LowerLegLeft, "XZ")
AlignBoneRotationOnPlane(MMD_LowerLegDLeft, GOH_LowerLegLeft, "YZ")
AlignBoneRotationOnPlane(MMD_LowerLegDLeft, GOH_LowerLegLeft, "XZ")

AlignBoneRotationOnPlane(MMD_LowerLegDRight, GOH_LowerLegRight, "YZ")
AlignBoneRotationOnPlane(MMD_LowerLegDRight, GOH_LowerLegRight, "XZ")
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
MMD_NeckSourceBone = GetNodeByNameRaiser(MMD_NeckBoneName)
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
ApplyRotationOnPlane(MMD_NeckSourceBone, -(UpperBodyDirectionDiff * ShoulderWeight), UpperBodyAlignmentPlane)

### Distribute scaling
#### Recacluate the Scale needed
GOH_UpperBodySourcePos = GetMeanPoseFromNodeNameList(GOH_UpperBodySourceList)
GOH_UpperBodyTargetPos = GetMeanPoseFromNodeNameList(GOH_UpperBodyTargetList)

MMD_UpperBodySourcePos = GetMeanPoseFromNodeNameList(MMD_UpperBodySourceList)
MMD_UpperBodyTargetPos = GetMeanPoseFromNodeNameList(MMD_UpperBodyTargetList)

LengthScaleNeeded = GetVectorLength(GOH_UpperBodyTargetPos - GOH_UpperBodySourcePos) / GetVectorLength(MMD_UpperBodyTargetPos - MMD_UpperBodySourcePos)

CumulativeShoulderScale = 1.0 # We record this value for further hip scaling

ScalingBones = list()
ScalingWeights = list()
for CurrentStepStartBones, CurrentStepEndBones, CurrentStepWeightRaw in UpperBodySteps[1:]: # MMD_UpperBodySourceList (Legs) DO NOT SCALE, so we used [1:]!
    ScalingBones.append(CurrentStepStartBones)
    ScalingWeights.append(CurrentStepWeightRaw)
ScalingFactor = SolveResizeChainRatio(ScalingWeights, LengthScaleNeeded, 32, 0.0, 10.0)

for ScalingBone, ScalingWeight in zip(ScalingBones, ScalingWeights):
    CurrentStepScaling = ScalingWeight * ScalingFactor
    CumulativeShoulderScale *= (CurrentStepScaling ** 0.5)
    for CurrentBone in CurrentStepStartBones:
        rt.scale(CurrentBone, rt.Point3((CurrentStepScaling ** 0.5), CurrentStepScaling, (CurrentStepScaling ** 0.5)))

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
MMD_NeckSourceBone.pos = GetNodeByNameRaiser(GOH_NeckBoneName).pos

#### Align shoulder here
GOH_ShoulderLeftName = "GFA_MWT_SKE_Hand1L"
GOH_ShoulderRightName = "GFA_MWT_SKE_Hand1R"
MMD_ShoulderLeftName = "ShoulderC_L"
MMD_ShoulderRightName = "ShoulderC_R"
MMD_LowerBodyName = "LowerBody"

ShoulderScaleBones = ["UpperBody", "UpperBody2"]
ShoulderScaleBonesTotalAmount = 0.667 # Ratio ** This amount
ShoulderScaleBonesLowerBodyAmount = 0.667 # Ratio ** This amount

GOH_ShoulderLeft = GetNodeByNameRaiser(GOH_ShoulderLeftName)
GOH_ShoulderRight = GetNodeByNameRaiser(GOH_ShoulderRightName)
MMD_ShoulderLeft = GetNodeByNameRaiser(MMD_ShoulderLeftName)
MMD_ShoulderRight = GetNodeByNameRaiser(MMD_ShoulderRightName)

GOH_ShoulderVector = GOH_ShoulderLeft.pos - GOH_ShoulderRight.pos
MMD_ShoulderVector = MMD_ShoulderLeft.pos - MMD_ShoulderRight.pos

ShoulderWidthRatio = GetVectorLength(GOH_ShoulderVector) / GetVectorLength(MMD_ShoulderVector)

### This scale should be opreated in WORLD
coordsys = getattr(pymxs.runtime, '%coordsys_context')
prev_coordsys = coordsys(pymxs.runtime.Name('world'), None)
ShoulderEachBoneScale = (ShoulderWidthRatio ** ShoulderScaleBonesTotalAmount) ** (1 / len(ShoulderScaleBones))
for BoneName in ShoulderScaleBones:
    rt.scale(GOH_ShoulderLeft, rt.Point3(ShoulderEachBoneScale**0.667,ShoulderEachBoneScale,ShoulderEachBoneScale**0.667))
    rt.scale(GOH_ShoulderRight, rt.Point3(ShoulderEachBoneScale**0.667,ShoulderEachBoneScale,ShoulderEachBoneScale**0.667))
# Restore previous coord
coordsys(prev_coordsys, None)

## Move Bones To Fit
MMD_ShoulderLeft.pos = GOH_ShoulderLeft.pos
MMD_ShoulderRight.pos = GOH_ShoulderRight.pos

### Scale LowerBody For Matching
UpperLegOrigCenter = (GetNodeByNameRaiser(MMD_UpperLegLeft[0]).pos + GetNodeByNameRaiser(MMD_UpperLegRight[0]).pos) / 2.0
LowerBodyScaling = (ShoulderWidthRatio * CumulativeShoulderScale) ** ShoulderScaleBonesLowerBodyAmount
rt.scale(GetNodeByNameRaiser(MMD_LowerBodyName), rt.Point3(LowerBodyScaling,ShoulderEachBoneScale,LowerBodyScaling))
UpperLegCurrCenter = (GetNodeByNameRaiser(MMD_UpperLegLeft[0]).pos + GetNodeByNameRaiser(MMD_UpperLegRight[0]).pos) / 2.0
### Normalize Lower Body, BREAK LINK
NormalizeScaleBreakLink(MMD_UpperLegLeft[0])
NormalizeScaleBreakLink(MMD_UpperLegRight[0])
NormalizeScaleBreakLink(MMD_UpperLegDLeft[0])
NormalizeScaleBreakLink(MMD_UpperLegDRight[0])
GetNodeByNameRaiser(MMD_UpperLegLeft[0]).pos = GetNodeByNameRaiser(MMD_UpperLegLeft[0]).pos + (UpperLegOrigCenter - UpperLegCurrCenter)
GetNodeByNameRaiser(MMD_UpperLegRight[0]).pos = GetNodeByNameRaiser(MMD_UpperLegRight[0]).pos + (UpperLegOrigCenter - UpperLegCurrCenter)
GetNodeByNameRaiser(MMD_UpperLegDLeft[0]).pos = GetNodeByNameRaiser(MMD_UpperLegDLeft[0]).pos + (UpperLegOrigCenter - UpperLegCurrCenter)
GetNodeByNameRaiser(MMD_UpperLegDRight[0]).pos = GetNodeByNameRaiser(MMD_UpperLegDRight[0]).pos + (UpperLegOrigCenter - UpperLegCurrCenter)




## UpperLeg: ReAlignment
## UpperLeg Scaling
AlignBoneLength(MMD_UpperLegLeft, GOH_UpperLegLeft, UpperLegScalingAxis)
AlignBoneLength(MMD_UpperLegRight, GOH_UpperLegRight, UpperLegScalingAxis)
AlignBoneLength(MMD_UpperLegDLeft, GOH_UpperLegLeft, UpperLegScalingAxis)
AlignBoneLength(MMD_UpperLegDRight, GOH_UpperLegRight, UpperLegScalingAxis)

## UpperLeg Rotation (YZ -> XZ)
AlignBoneRotationOnPlane(MMD_UpperLegLeft, GOH_UpperLegLeft, "YZ")
AlignBoneRotationOnPlane(MMD_UpperLegLeft, GOH_UpperLegLeft, "XZ")
AlignBoneRotationOnPlane(MMD_UpperLegLeft, GOH_UpperLegLeft, "YZ")
AlignBoneRotationOnPlane(MMD_UpperLegLeft, GOH_UpperLegLeft, "XZ")

AlignBoneRotationOnPlane(MMD_UpperLegRight, GOH_UpperLegRight, "YZ")
AlignBoneRotationOnPlane(MMD_UpperLegRight, GOH_UpperLegRight, "XZ")
AlignBoneRotationOnPlane(MMD_UpperLegRight, GOH_UpperLegRight, "YZ")
AlignBoneRotationOnPlane(MMD_UpperLegRight, GOH_UpperLegRight, "XZ")

AlignBoneRotationOnPlane(MMD_UpperLegDLeft, GOH_UpperLegLeft, "YZ")
AlignBoneRotationOnPlane(MMD_UpperLegDLeft, GOH_UpperLegLeft, "XZ")
AlignBoneRotationOnPlane(MMD_UpperLegDLeft, GOH_UpperLegLeft, "YZ")
AlignBoneRotationOnPlane(MMD_UpperLegDLeft, GOH_UpperLegLeft, "XZ")

AlignBoneRotationOnPlane(MMD_UpperLegDRight, GOH_UpperLegRight, "YZ")
AlignBoneRotationOnPlane(MMD_UpperLegDRight, GOH_UpperLegRight, "XZ")
AlignBoneRotationOnPlane(MMD_UpperLegDRight, GOH_UpperLegRight, "YZ")
AlignBoneRotationOnPlane(MMD_UpperLegDRight, GOH_UpperLegRight, "XZ")

### LowerLeg: ReAlignment

## LowerLeg: Scaling Y -> Rotation YZ -> Rotation XZ
## LowerLeg Scaling
AlignBoneLength(MMD_LowerLegLeft, GOH_LowerLegLeft, LowerLegScalingAxis, LengthRatioToTarget=0.925)
AlignBoneLength(MMD_LowerLegRight, GOH_LowerLegRight, LowerLegScalingAxis, LengthRatioToTarget=0.925)
AlignBoneLength(MMD_LowerLegDLeft, GOH_LowerLegLeft, LowerLegScalingAxis, LengthRatioToTarget=0.925)
AlignBoneLength(MMD_LowerLegDRight, GOH_LowerLegRight, LowerLegScalingAxis, LengthRatioToTarget=0.925)

## LowerLeg Rotation (YZ -> XZ)
AlignBoneRotationOnPlane(MMD_LowerLegLeft, GOH_LowerLegLeft, "YZ")
AlignBoneRotationOnPlane(MMD_LowerLegLeft, GOH_LowerLegLeft, "XZ")
AlignBoneRotationOnPlane(MMD_LowerLegLeft, GOH_LowerLegLeft, "YZ")
AlignBoneRotationOnPlane(MMD_LowerLegLeft, GOH_LowerLegLeft, "XZ")

AlignBoneRotationOnPlane(MMD_LowerLegRight, GOH_LowerLegRight, "YZ")
AlignBoneRotationOnPlane(MMD_LowerLegRight, GOH_LowerLegRight, "XZ")
AlignBoneRotationOnPlane(MMD_LowerLegRight, GOH_LowerLegRight, "YZ")
AlignBoneRotationOnPlane(MMD_LowerLegRight, GOH_LowerLegRight, "XZ")

AlignBoneRotationOnPlane(MMD_LowerLegDLeft, GOH_LowerLegLeft, "YZ")
AlignBoneRotationOnPlane(MMD_LowerLegDLeft, GOH_LowerLegLeft, "XZ")
AlignBoneRotationOnPlane(MMD_LowerLegDLeft, GOH_LowerLegLeft, "YZ")
AlignBoneRotationOnPlane(MMD_LowerLegDLeft, GOH_LowerLegLeft, "XZ")

AlignBoneRotationOnPlane(MMD_LowerLegDRight, GOH_LowerLegRight, "YZ")
AlignBoneRotationOnPlane(MMD_LowerLegDRight, GOH_LowerLegRight, "XZ")
AlignBoneRotationOnPlane(MMD_LowerLegDRight, GOH_LowerLegRight, "YZ")
AlignBoneRotationOnPlane(MMD_LowerLegDRight, GOH_LowerLegRight, "XZ")

## UpperLeg Re-Rotation To Match Foot Pos

GOH_LegFinalLeft = ("Leg_L", "GFA_MWT_SKE_foot3L")
GOH_LegFinalRight = ("Leg_R", "GFA_MWT_SKE_foot3R")

MMD_LegFinalLeft = ("Leg_L", "Ankle_L")
MMD_LegFinalRight = ("Leg_R", "Ankle_R")
MMD_LegFinalDLeft = ("LegD_L", "AnkleD_L") # Why is there a "D" postfixed version?
MMD_LegFinalDRight = ("LegD_R", "AnkleD_R") # Why is there a "D" postfixed version?

AlignBoneRotationOnPlane(MMD_LegFinalLeft, GOH_LegFinalLeft, "YZ")
AlignBoneRotationOnPlane(MMD_LegFinalLeft, GOH_LegFinalLeft, "XZ")
AlignBoneRotationOnPlane(MMD_LegFinalDLeft, GOH_LegFinalLeft, "YZ")
AlignBoneRotationOnPlane(MMD_LegFinalDLeft, GOH_LegFinalLeft, "XZ")
AlignBoneRotationOnPlane(MMD_LegFinalRight, GOH_LegFinalRight, "YZ")
AlignBoneRotationOnPlane(MMD_LegFinalRight, GOH_LegFinalRight, "XZ")
AlignBoneRotationOnPlane(MMD_LegFinalDRight, GOH_LegFinalRight, "YZ")
AlignBoneRotationOnPlane(MMD_LegFinalDRight, GOH_LegFinalRight, "XZ")

## Normalize Foot Scale, BREAK LINK
NormalizeScaleBreakLink(MMD_LowerLegLeft[1])
NormalizeScaleBreakLink(MMD_LowerLegRight[1])
NormalizeScaleBreakLink(MMD_LowerLegDLeft[1])
NormalizeScaleBreakLink(MMD_LowerLegDRight[1])

#### Align UpperArm
### UpperArm
GOH_UpperArmLeft = ("GFA_MWT_SKE_Hand1L", "GFA_MWT_SKE_Hand2L")
GOH_UpperArmRight = ("GFA_MWT_SKE_Hand1R", "GFA_MWT_SKE_Hand2R")

MMD_UpperArmLeft = ("Arm_L", "Elbow_L")
MMD_UpperArmRight = ("Arm_R", "Elbow_R")

UpperArmScalingAxis = "Y"

## Normalize Scle, Break link For Shoulders and Neck
for CurrentBone in UpperBodySteps[-1][1]: # Last step end bones
    NormalizeScaleBreakLink(CurrentBone.name)
NormalizeScaleBreakLink(MMD_NeckBoneName)

## UpperBody Extra Scaling
UpperBodyExtraScale = max(MMD_NeckSourceBone.scale) / max(GetNodeByNameRaiser(MMD_UpperLegLeft[0]).scale)
UpperBodyExtraScaleFittingShoulder = (1 / UpperBodyExtraScale) ** 0.5
UpperBodyExtraScaleFittingHead = (1 / UpperBodyExtraScale) ** 0.625
for CurrentBone in UpperBodySteps[-1][1]: # Last step end bones
    rt.scale(CurrentBone, rt.Point3(UpperBodyExtraScaleFittingShoulder, UpperBodyExtraScaleFittingShoulder, UpperBodyExtraScaleFittingShoulder))
rt.scale(MMD_NeckSourceBone, rt.Point3(UpperBodyExtraScaleFittingHead, UpperBodyExtraScaleFittingHead, UpperBodyExtraScaleFittingHead))
## Neck Offset
MMD_NeckSourceBoneName = "UpperBody"
NeckBoneVector = MMD_NeckSourceBone.pos - GetNodeByNameRaiser(MMD_NeckSourceBoneName).pos
MMD_NeckSourceBone.pos = GetNodeByNameRaiser(MMD_NeckSourceBoneName).pos + (NeckBoneVector * 0.96875)

## UpperArm: Scaling Y -> Rotation YZ -> Rotation XZ
### UpperArm Scaling
AlignBoneLength(MMD_UpperArmLeft, GOH_UpperArmLeft, UpperArmScalingAxis)
AlignBoneLength(MMD_UpperArmRight, GOH_UpperArmRight, UpperArmScalingAxis)

### UpperArm Rotation (YZ -> XZ)
AlignBoneRotationOnPlane(MMD_UpperArmLeft, GOH_UpperArmLeft, "XY")
AlignBoneRotationOnPlane(MMD_UpperArmLeft, GOH_UpperArmLeft, "YZ")
AlignBoneRotationOnPlane(MMD_UpperArmLeft, GOH_UpperArmLeft, "XY")
AlignBoneRotationOnPlane(MMD_UpperArmLeft, GOH_UpperArmLeft, "YZ")

AlignBoneRotationOnPlane(MMD_UpperArmRight, GOH_UpperArmRight, "XY")
AlignBoneRotationOnPlane(MMD_UpperArmRight, GOH_UpperArmRight, "YZ")
AlignBoneRotationOnPlane(MMD_UpperArmRight, GOH_UpperArmRight, "XY")
AlignBoneRotationOnPlane(MMD_UpperArmRight, GOH_UpperArmRight, "YZ")

### LowerArm
GOH_LowerArmLeft = ("GFA_MWT_SKE_Hand2L", "GFA_MWT_SKE_Hand_rot1L")
GOH_LowerArmRight = ("GFA_MWT_SKE_Hand2R", "GFA_MWT_SKE_Hand_rot1R")

MMD_LowerArmLeft = ("Elbow_L", "Wrist_L")
MMD_LowerArmRight = ("Elbow_R", "Wrist_R")

LowerArmScalingAxis = "Y"

## LowerArm: Scaling Y -> Rotation YZ -> Rotation XZ
### LowerArm Scaling
AlignBoneLength(MMD_LowerArmLeft, GOH_LowerArmLeft, LowerArmScalingAxis)
AlignBoneLength(MMD_LowerArmRight, GOH_LowerArmRight, LowerArmScalingAxis)

### LowerArm Rotation (YZ -> XZ)
AlignBoneRotationOnPlane(MMD_LowerArmLeft, GOH_LowerArmLeft, "YZ")
AlignBoneRotationOnPlane(MMD_LowerArmLeft, GOH_LowerArmLeft, "XY")

AlignBoneRotationOnPlane(MMD_LowerArmLeft, GOH_LowerArmLeft, "YZ")
AlignBoneRotationOnPlane(MMD_LowerArmLeft, GOH_LowerArmLeft, "XY")

AlignBoneRotationOnPlane(MMD_LowerArmRight, GOH_LowerArmRight, "YZ")
AlignBoneRotationOnPlane(MMD_LowerArmRight, GOH_LowerArmRight, "XY")

AlignBoneRotationOnPlane(MMD_LowerArmRight, GOH_LowerArmRight, "YZ")
AlignBoneRotationOnPlane(MMD_LowerArmRight, GOH_LowerArmRight, "XY")

### FingerAlignment
MMD_IndexFinger_L1 = ("IndexFinger1_L", "IndexFinger2_L")
MMD_IndexFinger_L2 = ("IndexFinger2_L", "IndexFinger3_L")
MMD_MiddleFinger_L1 = ("MiddleFinger1_L", "MiddleFinger2_L")
MMD_MiddleFinger_L2 = ("MiddleFinger2_L", "MiddleFinger3_L")
MMD_LittleFinger_L1 = ("LittleFinger1_L", "LittleFinger2_L")
MMD_LittleFinger_L2 = ("LittleFinger2_L", "LittleFinger3_L")
MMD_RingFinger_L1 = ("RingFinger1_L", "RingFinger2_L")
MMD_RingFinger_L2 = ("RingFinger2_L", "RingFinger3_L")
MMD_Thumb_L1 = ("Thumb0_L", "Thumb1_L")
MMD_Thumb_L2 = ("Thumb1_L", "Thumb2_L")

MMD_IndexFinger_R1 = ("IndexFinger1_R", "IndexFinger2_R")
MMD_IndexFinger_R2 = ("IndexFinger2_R", "IndexFinger3_R")
MMD_MiddleFinger_R1 = ("MiddleFinger1_R", "MiddleFinger2_R")
MMD_MiddleFinger_R2 = ("MiddleFinger2_R", "MiddleFinger3_R")
MMD_LittleFinger_R1 = ("LittleFinger1_R", "LittleFinger2_R")
MMD_LittleFinger_R2 = ("LittleFinger2_R", "LittleFinger3_R")
MMD_RingFinger_R1 = ("RingFinger1_R", "RingFinger2_R")
MMD_RingFinger_R2 = ("RingFinger2_R", "RingFinger3_R")
MMD_Thumb_R1 = ("Thumb0_R", "Thumb1_R")
MMD_Thumb_R2 = ("Thumb1_R", "Thumb2_R")

GOH_FingerRotation = -45 # ?

AlignBoneRotationOnPlane(MMD_IndexFinger_L1, MMD_LowerArmLeft, "XY")
AlignBoneRotationOnPlane(MMD_IndexFinger_L1, MMD_LowerArmLeft, "YZ")
AlignBoneRotationOnPlane(MMD_IndexFinger_L2, MMD_LowerArmLeft, "XY")
AlignBoneRotationOnPlane(MMD_IndexFinger_L2, MMD_LowerArmLeft, "YZ")
AlignBoneRotationOnPlane(MMD_MiddleFinger_L1, MMD_LowerArmLeft, "XY")
AlignBoneRotationOnPlane(MMD_MiddleFinger_L1, MMD_LowerArmLeft, "YZ")
AlignBoneRotationOnPlane(MMD_MiddleFinger_L2, MMD_LowerArmLeft, "XY")
AlignBoneRotationOnPlane(MMD_MiddleFinger_L2, MMD_LowerArmLeft, "YZ")
AlignBoneRotationOnPlane(MMD_LittleFinger_L1, MMD_LowerArmLeft, "XY")
AlignBoneRotationOnPlane(MMD_LittleFinger_L1, MMD_LowerArmLeft, "YZ")
AlignBoneRotationOnPlane(MMD_LittleFinger_L2, MMD_LowerArmLeft, "XY")
AlignBoneRotationOnPlane(MMD_LittleFinger_L2, MMD_LowerArmLeft, "YZ")
AlignBoneRotationOnPlane(MMD_RingFinger_L1, MMD_LowerArmLeft, "XY")
AlignBoneRotationOnPlane(MMD_RingFinger_L1, MMD_LowerArmLeft, "YZ")
AlignBoneRotationOnPlane(MMD_RingFinger_L2, MMD_LowerArmLeft, "XY")
AlignBoneRotationOnPlane(MMD_RingFinger_L2, MMD_LowerArmLeft, "YZ")

AlignBoneRotationOnPlane(MMD_IndexFinger_R1, MMD_LowerArmRight, "XY")
AlignBoneRotationOnPlane(MMD_IndexFinger_R1, MMD_LowerArmRight, "YZ")
AlignBoneRotationOnPlane(MMD_IndexFinger_R2, MMD_LowerArmRight, "XY")
AlignBoneRotationOnPlane(MMD_IndexFinger_R2, MMD_LowerArmRight, "YZ")
AlignBoneRotationOnPlane(MMD_MiddleFinger_R1, MMD_LowerArmRight, "XY")
AlignBoneRotationOnPlane(MMD_MiddleFinger_R1, MMD_LowerArmRight, "YZ")
AlignBoneRotationOnPlane(MMD_MiddleFinger_R2, MMD_LowerArmRight, "XY")
AlignBoneRotationOnPlane(MMD_MiddleFinger_R2, MMD_LowerArmRight, "YZ")
AlignBoneRotationOnPlane(MMD_LittleFinger_R1, MMD_LowerArmRight, "XY")
AlignBoneRotationOnPlane(MMD_LittleFinger_R1, MMD_LowerArmRight, "YZ")
AlignBoneRotationOnPlane(MMD_LittleFinger_R2, MMD_LowerArmRight, "XY")
AlignBoneRotationOnPlane(MMD_LittleFinger_R2, MMD_LowerArmRight, "YZ")
AlignBoneRotationOnPlane(MMD_RingFinger_R1, MMD_LowerArmRight, "XY")
AlignBoneRotationOnPlane(MMD_RingFinger_R1, MMD_LowerArmRight, "YZ")
AlignBoneRotationOnPlane(MMD_RingFinger_R2, MMD_LowerArmRight, "XY")
AlignBoneRotationOnPlane(MMD_RingFinger_R2, MMD_LowerArmRight, "YZ")

ApplyRotationOnLocalAxisByName(MMD_IndexFinger_L1[0], GOH_FingerRotation, "X")
ApplyRotationOnLocalAxisByName(MMD_IndexFinger_L2[0], GOH_FingerRotation, "X")
ApplyRotationOnLocalAxisByName(MMD_IndexFinger_L2[1], GOH_FingerRotation, "X")

ApplyRotationOnLocalAxisByName(MMD_MiddleFinger_L1[0], GOH_FingerRotation, "X")
ApplyRotationOnLocalAxisByName(MMD_MiddleFinger_L2[0], GOH_FingerRotation, "X")
ApplyRotationOnLocalAxisByName(MMD_MiddleFinger_L2[1], GOH_FingerRotation, "X")

ApplyRotationOnLocalAxisByName(MMD_LittleFinger_L1[0], GOH_FingerRotation, "X")
ApplyRotationOnLocalAxisByName(MMD_LittleFinger_L2[0], GOH_FingerRotation, "X")
ApplyRotationOnLocalAxisByName(MMD_LittleFinger_L2[1], GOH_FingerRotation, "X")

ApplyRotationOnLocalAxisByName(MMD_RingFinger_L1[0], GOH_FingerRotation, "X")
ApplyRotationOnLocalAxisByName(MMD_RingFinger_L2[0], GOH_FingerRotation, "X")
ApplyRotationOnLocalAxisByName(MMD_RingFinger_L2[1], GOH_FingerRotation, "X")


ApplyRotationOnLocalAxisByName(MMD_IndexFinger_R1[0], -GOH_FingerRotation, "X")
ApplyRotationOnLocalAxisByName(MMD_IndexFinger_R2[0], -GOH_FingerRotation, "X")
ApplyRotationOnLocalAxisByName(MMD_IndexFinger_R2[1], -GOH_FingerRotation, "X")

ApplyRotationOnLocalAxisByName(MMD_MiddleFinger_R1[0], -GOH_FingerRotation, "X")
ApplyRotationOnLocalAxisByName(MMD_MiddleFinger_R2[0], -GOH_FingerRotation, "X")
ApplyRotationOnLocalAxisByName(MMD_MiddleFinger_R2[1], -GOH_FingerRotation, "X")

ApplyRotationOnLocalAxisByName(MMD_LittleFinger_R1[0], -GOH_FingerRotation, "X")
ApplyRotationOnLocalAxisByName(MMD_LittleFinger_R2[0], -GOH_FingerRotation, "X")
ApplyRotationOnLocalAxisByName(MMD_LittleFinger_R2[1], -GOH_FingerRotation, "X")

ApplyRotationOnLocalAxisByName(MMD_RingFinger_R1[0], -GOH_FingerRotation, "X")
ApplyRotationOnLocalAxisByName(MMD_RingFinger_R2[0], -GOH_FingerRotation, "X")
ApplyRotationOnLocalAxisByName(MMD_RingFinger_R2[1], -GOH_FingerRotation, "X")

MMD_IndexFinger_LA = ("IndexFinger1_L", "IndexFinger3_L")
MMD_MiddleFinger_LA = ("MiddleFinger1_L", "MiddleFinger3_L")
MMD_LittleFinger_LA = ("LittleFinger1_L", "LittleFinger3_L")
MMD_RingFinger_LA = ("RingFinger1_L", "RingFinger3_L")

MMD_IndexFinger_RA = ("IndexFinger1_R", "IndexFinger3_R")
MMD_MiddleFinger_RA = ("MiddleFinger1_R", "MiddleFinger3_R")
MMD_LittleFinger_RA = ("LittleFinger1_R", "LittleFinger3_R")
MMD_RingFinger_RA = ("RingFinger1_R", "RingFinger3_R")

AlignBoneRotationOnPlane(MMD_IndexFinger_LA, MMD_MiddleFinger_LA, "XY")
AlignBoneRotationOnPlane(MMD_LittleFinger_LA, MMD_MiddleFinger_LA, "XY")
AlignBoneRotationOnPlane(MMD_RingFinger_LA, MMD_MiddleFinger_LA, "XY")
AlignBoneRotationOnPlane(MMD_IndexFinger_RA, MMD_MiddleFinger_RA, "XY")
AlignBoneRotationOnPlane(MMD_LittleFinger_RA, MMD_MiddleFinger_RA, "XY")
AlignBoneRotationOnPlane(MMD_RingFinger_RA, MMD_MiddleFinger_RA, "XY")

AlignBoneRotationOnPlane(MMD_IndexFinger_L1, MMD_MiddleFinger_L1, "XZ")
AlignBoneRotationOnPlane(MMD_LittleFinger_L1, MMD_MiddleFinger_L1, "XZ")
AlignBoneRotationOnPlane(MMD_RingFinger_L1, MMD_MiddleFinger_L1, "XZ")
AlignBoneRotationOnPlane(MMD_IndexFinger_R1, MMD_MiddleFinger_R1, "XZ")
AlignBoneRotationOnPlane(MMD_LittleFinger_R1, MMD_MiddleFinger_R1, "XZ")
AlignBoneRotationOnPlane(MMD_RingFinger_R1, MMD_MiddleFinger_R1, "XZ")

AlignBoneRotationOnPlane(MMD_IndexFinger_L1, MMD_MiddleFinger_L1, "YZ")
AlignBoneRotationOnPlane(MMD_LittleFinger_L1, MMD_MiddleFinger_L1, "YZ")
AlignBoneRotationOnPlane(MMD_RingFinger_L1, MMD_MiddleFinger_L1, "YZ")
AlignBoneRotationOnPlane(MMD_IndexFinger_R1, MMD_MiddleFinger_R1, "YZ")
AlignBoneRotationOnPlane(MMD_LittleFinger_R1, MMD_MiddleFinger_R1, "YZ")
AlignBoneRotationOnPlane(MMD_RingFinger_R1, MMD_MiddleFinger_R1, "YZ")

AlignBoneRotationOnPlane(MMD_IndexFinger_L2, MMD_MiddleFinger_L2, "XY")
AlignBoneRotationOnPlane(MMD_LittleFinger_L2, MMD_MiddleFinger_L2, "XY")
AlignBoneRotationOnPlane(MMD_RingFinger_L2, MMD_MiddleFinger_L2, "XY")
AlignBoneRotationOnPlane(MMD_IndexFinger_R2, MMD_MiddleFinger_R2, "XY")
AlignBoneRotationOnPlane(MMD_LittleFinger_R2, MMD_MiddleFinger_R2, "XY")
AlignBoneRotationOnPlane(MMD_RingFinger_R2, MMD_MiddleFinger_R2, "XY")

AlignBoneRotationOnPlane(MMD_IndexFinger_L2, MMD_MiddleFinger_L2, "XZ")
AlignBoneRotationOnPlane(MMD_LittleFinger_L2, MMD_MiddleFinger_L2, "XZ")
AlignBoneRotationOnPlane(MMD_RingFinger_L2, MMD_MiddleFinger_L2, "XZ")
AlignBoneRotationOnPlane(MMD_IndexFinger_R2, MMD_MiddleFinger_R2, "XZ")
AlignBoneRotationOnPlane(MMD_LittleFinger_R2, MMD_MiddleFinger_R2, "XZ")
AlignBoneRotationOnPlane(MMD_RingFinger_R2, MMD_MiddleFinger_R2, "XZ")

AlignBoneRotationOnPlane(MMD_IndexFinger_L2, MMD_MiddleFinger_L2, "YZ")
AlignBoneRotationOnPlane(MMD_LittleFinger_L2, MMD_MiddleFinger_L2, "YZ")
AlignBoneRotationOnPlane(MMD_RingFinger_L2, MMD_MiddleFinger_L2, "YZ")
AlignBoneRotationOnPlane(MMD_IndexFinger_R2, MMD_MiddleFinger_R2, "YZ")
AlignBoneRotationOnPlane(MMD_LittleFinger_R2, MMD_MiddleFinger_R2, "YZ")
AlignBoneRotationOnPlane(MMD_RingFinger_R2, MMD_MiddleFinger_R2, "YZ")

# Further Align Arm to align hand.
MMD_FullArmWithHand_L = ("Arm_L", "MiddleFinger2_L")
GOH_FullArmWithHand_L = ("GFA_MWT_SKE_Hand1L", "GFA_MWT_SKE_Palm4L_hide")
MMD_FullArmWithHand_R = ("Arm_R", "MiddleFinger2_R")
GOH_FullArmWithHand_R = ("GFA_MWT_SKE_Hand1R", "GFA_MWT_SKE_Palm4R_hide")

AlignBoneRotationOnPlane(MMD_FullArmWithHand_L, GOH_FullArmWithHand_L, "YZ")
AlignBoneRotationOnPlane(MMD_FullArmWithHand_R, GOH_FullArmWithHand_R, "YZ")
AlignBoneRotationOnPlane(MMD_FullArmWithHand_L, GOH_FullArmWithHand_L, "XY")
AlignBoneRotationOnPlane(MMD_FullArmWithHand_R, GOH_FullArmWithHand_R, "XY")

MMD_LowerArmWithHand_L = ("Elbow_L", "MiddleFinger2_L")
GOH_LowerArmWithHand_L = ("GFA_MWT_SKE_Hand2L", "GFA_MWT_SKE_Palm4L_hide")
MMD_LowerArmWithHand_R = ("Elbow_R", "MiddleFinger2_R")
GOH_LowerArmWithHand_R = ("GFA_MWT_SKE_Hand2R", "GFA_MWT_SKE_Palm4R_hide")

AlignBoneLength(MMD_LowerArmWithHand_L, GOH_LowerArmWithHand_L, LowerArmScalingAxis)
AlignBoneLength(MMD_LowerArmWithHand_R, GOH_LowerArmWithHand_R, LowerArmScalingAxis)


NormalizeScaleBreakLink("Wrist_L")
NormalizeScaleBreakLink("Wrist_R")

MMD_LowerWristToHand_L = ("Wrist_L", "MiddleFinger2_L")
GOH_LowerWristToHand_L = ("Wrist_L", "GFA_MWT_SKE_Palm4L_hide")
MMD_LowerWristToHand_R = ("Wrist_R", "MiddleFinger2_R")
GOH_LowerWristToHand_R = ("Wrist_R", "GFA_MWT_SKE_Palm4R_hide")

AlignBoneLength(MMD_LowerWristToHand_L, GOH_LowerWristToHand_L, "Y", OtherAxisScaleFactor=1.0)
AlignBoneLength(MMD_LowerWristToHand_R, GOH_LowerWristToHand_R, "Y", OtherAxisScaleFactor=1.0)



# LegTipEX_L, Heel Adjustment
