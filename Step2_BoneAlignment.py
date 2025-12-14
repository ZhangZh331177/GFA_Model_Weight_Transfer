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

def GetMeanPosFromNodeNameList(InputNodeNameList):
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

def GetBoneLength(TargetBoneNames):
    return(GetVectorLength(GetPosFromNodeName(TargetBoneNames[1]) - GetPosFromNodeName(TargetBoneNames[0])))

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

def ApplyRotationOnWorldAxis(TargetBone, Angle, Axis):
    coordsys = getattr(pymxs.runtime, '%coordsys_context')
    prev_coordsys = coordsys(pymxs.runtime.Name('world'), None)

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

def AlignBoneRotationOnPlaneBySequence(RotatingBone, TargetBone, PlaneSeq):
    for Plane in PlaneSeq:
        AlignBoneRotationOnPlane(RotatingBone, TargetBone, Plane)

def ApplyScaleOnLocalAxis(ScalingBone, LengthRatio, LocalAxis, OtherAxisScaleFactor = 0.5):
    # Apply Scaling
    ## Use local coords to scale
    coordsys = getattr(pymxs.runtime, '%coordsys_context')
    prev_coordsys = coordsys(pymxs.runtime.Name('local'), None)

    MainScale = LengthRatio
    OtherScale = LengthRatio ** OtherAxisScaleFactor
    # CurrentScale = ScalingBoneStart.scale
    if LocalAxis == "X":
        rt.scale(ScalingBone, rt.Point3(MainScale,OtherScale,OtherScale))
    elif LocalAxis == "Y":
        rt.scale(ScalingBone, rt.Point3(OtherScale,MainScale,OtherScale))
    elif LocalAxis == "Z":
        rt.scale(ScalingBone, rt.Point3(OtherScale,OtherScale,MainScale))
    else:
        raise ValueError("LocalAxis should be one of 'X', 'Y' or 'Z', Input value is '"+LocalAxis+"'!")
    
    # Restore previous coord
    coordsys(prev_coordsys, None)

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
        ApplyScaleOnLocalAxis(ScalingBoneStart, LengthRatio, MainLocalAxis, OtherAxisScaleFactor = OtherAxisScaleFactor)
    except Exception as e:
        Bone_A_Str = "'" + ScalingBone[0] + "','" + ScalingBone[1] + "'"
        Bone_B_Str = "'" + TargetBone[0] + "','" + TargetBone[1] + "'"
        raise RuntimeError("AlignBoneLength Raised Error: Failed to align Bone ["+Bone_A_Str+"] to Bone ["+Bone_B_Str+"] due to following exception:" + str(e))

def GetMeanScale(InputBoneName):
    InputBone = GetNodeByNameRaiser(InputBoneName)
    CurrentScale = InputBone.scale
    return abs(CurrentScale.x * CurrentScale.y * CurrentScale.z) ** (1.0 / 3.0)

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

def GetVectorMainAxis(StartNodeNameList, EndNodeNameList):
    InputVector = GetMeanPosFromNodeNameList(EndNodeNameList) - GetMeanPosFromNodeNameList(StartNodeNameList)
    X = InputVector.x
    Y = InputVector.y
    Z = InputVector.z
    if abs(X) >= abs(Y) and abs(X) >= abs(Z):
        if(X) > 0:
            return("+", "X")
        else:
            return("-", "X")
    elif abs(Y) >= abs(X) and abs(Y) >= abs(Z):
        if(Y) > 0:
            return("+", "Y")
        else:
            return("-", "Y")
    else:
        if(Z) > 0:
            return("+", "Z")
        else:
            return("-", "Z")

def GetChildPosDiffWihtParentRotation(ChildObject, ParentObject, Rotation, LocalAxis, RotateBack = True):
    OriginalChildPos = ChildObject.pos
    ApplyRotationOnLocalAxis(ParentObject, Rotation, LocalAxis)
    RotatedChildPos = ChildObject.pos
    if RotateBack:
        ApplyRotationOnLocalAxis(ParentObject, -Rotation, LocalAxis)
    return RotatedChildPos - OriginalChildPos

def GetPoseValueByAxis(InputPos, InputAxis):
    AxisDir, AxisName = InputAxis
    if AxisName == "X":
        ReturnValue =  InputPos.x
    elif AxisName == "Y":
        ReturnValue =  InputPos.y
    elif AxisName == "Z":
        ReturnValue =  InputPos.z
    else:
        raise ValueError("Name of InputAxis is not in XYZ !")
    
    if AxisDir == "+":
        return ReturnValue
    elif AxisDir == "-":
        return -ReturnValue
    else:
        raise ValueError("Direction of InputAxis is not + nor - !")

def GetExpectedRotationAxis(BoneName, FrontAxis, UpAxis):
    FrontAxisDir, FrontAxisName = FrontAxis
    # Create a dummy object and attach to Current Bone
    CurrentObject = GetNodeByNameRaiser(BoneName)
    DummyObject = rt.Dummy()

    if FrontAxisDir == "+":
        OffsetValue = 10.0
    elif FrontAxisDir == "-":
        OffsetValue = -10.0
    else:
        raise ValueError("Direction of FrontAis is not + nor - !")
    
    if FrontAxisName == "X":
        DummyObject.pos = CurrentObject.pos + rt.Point3(OffsetValue, 0, 0)
    elif FrontAxisName == "Y":
        DummyObject.pos = CurrentObject.pos + rt.Point3(0, OffsetValue, 0)
    elif FrontAxisName == "Z":
        DummyObject.pos = CurrentObject.pos + rt.Point3(0, 0, OffsetValue)
    else:
        raise ValueError("Name of FrontAxis is not in XYZ !")
    
    DummyObject.parent = CurrentObject

    AxisOffsetList = list()
    for AxisName in ["X", "Y", "Z"]:
        for AxisDir, CurrentRotation in zip(["+", "-"], [+45, -45]):
            CurrentRotateOffset = GetChildPosDiffWihtParentRotation(DummyObject, CurrentObject, CurrentRotation, AxisName, RotateBack = True)
            CurrentRotateOffsetValue = GetPoseValueByAxis(CurrentRotateOffset, UpAxis)
            AxisOffsetList.append([[AxisDir, AxisName], CurrentRotateOffsetValue])
    
    AxisOffsetList.sort(key=lambda x: x[1])
    rt.delete(DummyObject)

    return AxisOffsetList[-1][0]


def AutoRotateFinger(FingerBoneChain, FingerPointingAxis, RotatingTowardsAxis, RotationAng):
    BoneRotationDict = dict()
    LastBoneCount = 1
    LastBoneRotationRatio = 0.5
    for FingerBone in FingerBoneChain:
        BoneRotationDict[FingerBone] = GetExpectedRotationAxis(FingerBone, FingerPointingAxis, RotatingTowardsAxis)
    
    for FingerBone in FingerBoneChain[:len(FingerBone) - LastBoneCount]:
        RotationAxisDir, RotationAxisName = BoneRotationDict[FingerBone]
        if RotationAxisDir == "+":
            ApplyRotationOnLocalAxisByName(FingerBone, RotationAng, RotationAxisName)
        elif RotationAxisDir == "-":
            ApplyRotationOnLocalAxisByName(FingerBone, -RotationAng, RotationAxisName)
        else:
            raise ValueError("RotationAxisDir is not + nor - !")
    
    LastBoneRotationAng = RotationAng * LastBoneRotationRatio
    for FingerBone in FingerBoneChain[len(FingerBone) - LastBoneCount:]:
        RotationAxisDir, RotationAxisName = BoneRotationDict[FingerBone]
        if RotationAxisDir == "+":
            ApplyRotationOnLocalAxisByName(FingerBone, LastBoneRotationAng, RotationAxisName)
        elif RotationAxisDir == "-":
            ApplyRotationOnLocalAxisByName(FingerBone, -LastBoneRotationAng, RotationAxisName)
        else:
            raise ValueError("RotationAxisDir is not + nor - !")
        # RotationAxisDir, RotationAxisName = GetExpectedRotationAxis(FingerBone, FingerPointingAxis, RotatingTowardsAxis)




if __name__ == "__main__":
    # We assume that both models are facing X+ (Right), and Head up to Z+ (UP), with foot contact the ground (Z=0)
    MMD_Source_Config = "GF2"
    MMD_RootName = "GirlsFrontline AlvaDefault"
    MMD_MeshName = "GirlsFrontline AlvaDefault_mesh"
    MMD_Root = GetNodeByNameRaiser(MMD_RootName)
    MMD_Mesh = GetNodeByNameRaiser(MMD_MeshName)
    MMD_ShoeIsBottom = True

    SourceConfigs = {"GF2"}
    if MMD_Source_Config not in SourceConfigs:
        raise ValueError("Unknown Source Config!")

    ## Axis Alignment
    GOH_Shoulder_LR = ("GFA_MWT_SKE_Hand1L", "GFA_MWT_SKE_Hand1R")
    GOH_Foot_LR = ("GFA_MWT_SKE_foot3L", "GFA_MWT_SKE_foot3R")
    MMD_Shoulder_LR = ("Arm_L", "Arm_R")
    MMD_Foots_LR = ("Ankle_L", "Ankle_R")

    GOHHeadAxisDir, GOHHeadAxisName = GetVectorMainAxis(GOH_Foot_LR, GOH_Shoulder_LR)
    MMDHeadAxisDir, MMDHeadAxisName = GetVectorMainAxis(MMD_Foots_LR, MMD_Shoulder_LR)
    if MMDHeadAxisName != GOHHeadAxisName:
        RotationAxis = ({"X", "Y", "Z"} - {MMDHeadAxisName, GOHHeadAxisName}).pop()
        ApplyRotationOnWorldAxis(MMD_Root, 90, RotationAxis)
        GOHHeadAxisDir, GOHHeadAxisName = GetVectorMainAxis(GOH_Foot_LR, GOH_Shoulder_LR)
        MMDHeadAxisDir, MMDHeadAxisName = GetVectorMainAxis(MMD_Foots_LR, MMD_Shoulder_LR)

    if MMDHeadAxisDir != GOHHeadAxisDir:
        RotationAxis = ({"X", "Y", "Z"} - {MMDHeadAxisName, GOHHeadAxisName}).pop()
        ApplyRotationOnWorldAxis(MMD_Root, 180, RotationAxis)
        GOHHeadAxisDir, GOHHeadAxisName = GetVectorMainAxis(GOH_Foot_LR, GOH_Shoulder_LR)
        MMDHeadAxisDir, MMDHeadAxisName = GetVectorMainAxis(MMD_Foots_LR, MMD_Shoulder_LR)

    GOHShoulderAxisDir, GOHShoulderName = GetVectorMainAxis([GOH_Shoulder_LR[0],], [GOH_Shoulder_LR[1],])
    MMDShoulderAxisDir, MMDShoulderName = GetVectorMainAxis([MMD_Shoulder_LR[0],], [MMD_Shoulder_LR[1],])
    
    if MMDShoulderName != GOHShoulderName:
        ApplyRotationOnWorldAxis(MMD_Root, 90, MMDHeadAxisName)
        GOHShoulderAxisDir, GOHShoulderName = GetVectorMainAxis([GOH_Shoulder_LR[0],], [GOH_Shoulder_LR[1],])
        MMDShoulderAxisDir, MMDShoulderName = GetVectorMainAxis([MMD_Shoulder_LR[0],], [MMD_Shoulder_LR[1],])
    
    if MMDShoulderAxisDir != GOHShoulderAxisDir:
        ApplyRotationOnWorldAxis(MMD_Root, 180, MMDHeadAxisName)

    ## Full body Pre-Alignment
    ## Lower Body Rotation Alignment

    ### UpperLeg Parameters
    UpperLegScalingAxis = "Y"
    UpperLegRotationSequence = ["YZ", "XZ"]
    GOH_UpperLegLeft = ("GFA_MWT_SKE_foot1L", "GFA_MWT_SKE_foot2L")
    GOH_UpperLegRight = ("GFA_MWT_SKE_foot1R", "GFA_MWT_SKE_foot2R")
    MMD_UpperLegLeft = ("Leg_L", "Knee_L")
    MMD_UpperLegRight = ("Leg_R", "Knee_R")
    MMD_UpperLegDLeft = ("LegD_L", "KneeD_L") # Why is there a "D" postfixed version?
    MMD_UpperLegDRight = ("LegD_R", "KneeD_R") # Why is there a "D" postfixed version?

    ### LowerLeg Parameters
    LowerLegScalingAxis = "Y"
    LowerLegRotationSequence = ["YZ", "XZ"]
    GOH_LowerLegLeft = ("GFA_MWT_SKE_foot2L", "GFA_MWT_SKE_foot3L")
    GOH_LowerLegRight = ("GFA_MWT_SKE_foot2R", "GFA_MWT_SKE_foot3R")

    MMD_LowerLegLeft = ("Knee_L", "Ankle_L")
    MMD_LowerLegRight = ("Knee_R", "Ankle_R")
    MMD_LowerLegDLeft = ("KneeD_L", "AnkleD_L") # Why is there a "D" postfixed version?
    MMD_LowerLegDRight = ("KneeD_R", "AnkleD_R") # Why is there a "D" postfixed version?

    # These Names SHOULD be fixed in different run

    ## Pre-Overall scaling: Lower Body Alignment
    ### UpperLeg Rotation (YZ -> XZ)
    AlignBoneRotationOnPlaneBySequence(MMD_UpperLegLeft, GOH_UpperLegLeft, UpperLegRotationSequence)
    AlignBoneRotationOnPlaneBySequence(MMD_UpperLegRight, GOH_UpperLegRight, UpperLegRotationSequence)
    AlignBoneRotationOnPlaneBySequence(MMD_UpperLegDLeft, GOH_UpperLegLeft, UpperLegRotationSequence)
    AlignBoneRotationOnPlaneBySequence(MMD_UpperLegDRight, GOH_UpperLegRight, UpperLegRotationSequence)

    ### LowerLeg Rotation (YZ -> XZ)
    AlignBoneRotationOnPlaneBySequence(MMD_LowerLegLeft, GOH_LowerLegLeft, UpperLegRotationSequence)
    AlignBoneRotationOnPlaneBySequence(MMD_LowerLegRight, GOH_LowerLegRight, UpperLegRotationSequence)
    AlignBoneRotationOnPlaneBySequence(MMD_LowerLegDLeft, GOH_LowerLegLeft, UpperLegRotationSequence)
    AlignBoneRotationOnPlaneBySequence(MMD_LowerLegDRight, GOH_LowerLegRight, UpperLegRotationSequence)

    ## Overall Alignment Parameters
    BodyAlignmentPlane = "XZ"
    GOH_Shoulder_Name_List = ["GFA_MWT_SKE_Hand1L", "GFA_MWT_SKE_Hand1R"]
    MMD_Shoulder_Name_List = ["Arm_R", "Arm_L"]
    GOH_ShoulderLeftName = "GFA_MWT_SKE_Hand1L"
    GOH_ShoulderRightName = "GFA_MWT_SKE_Hand1R"
    MMD_ShoulderLeftName = "ShoulderC_L"
    MMD_ShoulderRightName = "ShoulderC_R"
    MMD_NeckBoneName = "Neck"
    MMD_HeadBoneName = "Head"
    GOH_NeckBoneName = "GFA_MWT_SKE_Head"

    ## Overall Scaling Alignment
    if (MMD_ShoeIsBottom):
        MMD_ShoulderHeight = GetMeanPosFromNodeNameList(MMD_Shoulder_Name_List).z - MMD_Mesh.min.z
    else:
        MMD_ShoulderHeight = GetMeanPosFromNodeNameList(MMD_Shoulder_Name_List).z
    
    GOH_ShoulderHeight = GetMeanPosFromNodeNameList(GOH_Shoulder_Name_List).z
    OverallScale = (GOH_ShoulderHeight / MMD_ShoulderHeight)

    rt.scale(MMD_Root, rt.point3(OverallScale, OverallScale, OverallScale))

    ### Overall Rotation Alignment
    GOH_FootCenterPos = GetMeanPosFromNodeNameList([GOH_LowerLegLeft[1], GOH_LowerLegRight[1]])
    GOH_ShoulderNeckCenterPos = GetMeanPosFromNodeNameList(GOH_Shoulder_Name_List + [MMD_NeckBoneName, MMD_NeckBoneName])
    GOH_BodyDirection = GetProjectedRotationOfPos(GOH_FootCenterPos, GOH_ShoulderNeckCenterPos, BodyAlignmentPlane)

    MMD_FootCenterPos = GetMeanPosFromNodeNameList([MMD_LowerLegLeft[1], MMD_LowerLegRight[1]])
    MMD_ShoulderNeckCenterPos = GetMeanPosFromNodeNameList(MMD_Shoulder_Name_List + [MMD_NeckBoneName, MMD_NeckBoneName])
    MMD_BodyDirection = GetProjectedRotationOfPos(MMD_FootCenterPos, MMD_ShoulderNeckCenterPos, BodyAlignmentPlane)

    BodyDirectionDiff = GOH_BodyDirection - MMD_BodyDirection # This will also be used in upper body alignment!
    ApplyRotationOnPlane(MMD_Root, GOH_BodyDirection - MMD_BodyDirection, BodyAlignmentPlane)

    ### Re-Align Legs Rotation
    for BoneName in [MMD_UpperLegLeft[0],MMD_UpperLegRight[0],MMD_UpperLegDLeft[0],MMD_UpperLegDRight[0]]:
        ApplyRotationOnPlane(GetNodeByNameRaiser(BoneName), -BodyDirectionDiff, BodyAlignmentPlane)

    ## Upper body alignment
    ### Upper body Alignment Parameters
    UpperBodyAlignmentPlane = "XZ"
    MMD_LowerBodyName = "LowerBody"
    MMD_UpperBodyChain = [
        ["Leg_L", "Leg_R"],
        ["UpperBody"],
        ["UpperBody2"],
        ["ShoulderP_L", "ShoulderP_R"]
    ]
    GOH_UpperBodySourceList = ["GFA_MWT_SKE_foot1L", "GFA_MWT_SKE_foot1R"]
    GOH_UpperBodyTargetList = ["GFA_MWT_SKE_Clavicle_left", "GFA_MWT_SKE_Clavicle_right"]
    
    ### Get the weight of each Step of upper body
    UpperBodyOverAllVector = GetMeanPosFromNodeNameList(MMD_UpperBodyChain[-1]) - GetMeanPosFromNodeNameList(MMD_UpperBodyChain[0])
    UpperBodySteps = list()
    TotalWeight = 0
    for i in range(1, len(MMD_UpperBodyChain)):
        CurrentStepVector = GetMeanPosFromNodeNameList(MMD_UpperBodyChain[i]) - GetMeanPosFromNodeNameList(MMD_UpperBodyChain[i-1])
        CurrentStepWeightRaw = GetProjectionLength(CurrentStepVector, UpperBodyOverAllVector)
        UpperBodySteps.append([MMD_UpperBodyChain[i-1], MMD_UpperBodyChain[i], CurrentStepWeightRaw])
        TotalWeight += CurrentStepWeightRaw

    ### Distribute Upper body rotation
    for CurrentStepStartBones, CurrentStepEndBones, CurrentStepWeightRaw in UpperBodySteps:
        CurrentStepWeight = CurrentStepWeightRaw / TotalWeight
        for CurrentBone in CurrentStepEndBones:
            ApplyRotationOnPlane(GetNodeByNameRaiser(CurrentBone), -(BodyDirectionDiff * CurrentStepWeight), UpperBodyAlignmentPlane)

    #### Also BackRotate the neck with the shoulder
    ShoulderWeight = UpperBodySteps[-1][-1] / TotalWeight
    ApplyRotationOnPlane(GetNodeByNameRaiser(MMD_NeckBoneName), -(BodyDirectionDiff * ShoulderWeight), UpperBodyAlignmentPlane)

    ### Distribute Upper body scaling
    #### Recacluate the Scale needed
    GOH_UpperBodyHeight = GetMeanPosFromNodeNameList(GOH_UpperBodyTargetList).z - GetMeanPosFromNodeNameList(GOH_UpperBodySourceList).z
    MMD_UpperBodyHeight = GetMeanPosFromNodeNameList(MMD_UpperBodyChain[-1]).z - GetMeanPosFromNodeNameList(MMD_UpperBodyChain[0]).z
    UpperBodyHeightScale = GOH_UpperBodyHeight / MMD_UpperBodyHeight

    GOH_ShoulderVector = GetNodeByNameRaiser(GOH_ShoulderLeftName).pos - GetNodeByNameRaiser(GOH_ShoulderRightName).pos
    MMD_ShoulderVector = GetNodeByNameRaiser(MMD_ShoulderLeftName).pos - GetNodeByNameRaiser(MMD_ShoulderRightName).pos
    UpperBodyWidthScale = GetVectorLength(GOH_ShoulderVector) / GetVectorLength(MMD_ShoulderVector)
    ## Z-scaling is only affect later bones, but Y-scaling is stacked, so there needs a seperated processing.
    ScalingBones = list()
    Y_TotalWeight = 0.0
    Y_ScalingByStep = list()
    Z_ScalingWeightByStep = list()
    #### Weight -> EndBone for Y_Axis, Distribute weights
    for CurrentStepStartBones, CurrentStepEndBones, CurrentStepWeightRaw in UpperBodySteps:
        ScalingBones.append(CurrentStepEndBones)
        Z_ScalingWeightByStep.append(CurrentStepWeightRaw)
        Y_TotalWeight += (CurrentStepWeightRaw)
    for CurrentStepStartBones, CurrentStepEndBones, CurrentStepWeightRaw in UpperBodySteps:
        Y_ScalingByStep.append(UpperBodyWidthScale ** ((CurrentStepWeightRaw)/Y_TotalWeight))
    #### Remove the first object in Z_ScalingWeightByStep, Add zero to its end
    #### Weight -> StartBone for Z_Axis, But skip first bone (Legs), so [W2,W3] Fit Bones [S2(E1), S3(E2)]
    #### Weight -> EndBone for Y_Axis, Not changed
    Z_ScalingFactor = SolveResizeChainRatio(Z_ScalingWeightByStep, UpperBodyHeightScale, 32, 0.0, 10.0)
    #### The first bone weight should be delivered to "LowerBody" Bone
    UpperBody_FirstStepScalingZ = Z_ScalingWeightByStep[0] * Z_ScalingFactor
    rt.scale(GetNodeByNameRaiser(MMD_LowerBodyName), rt.Point3(UpperBody_FirstStepScalingZ, UpperBody_FirstStepScalingZ, UpperBody_FirstStepScalingZ))
    #### Overall Position Alignment
    GOH_FullBodyAlignmentPos = GetMeanPosFromNodeNameList([GOH_UpperLegLeft[0], GOH_UpperLegRight[0]])
    MMD_FullBodyAlignmentPos = GetMeanPosFromNodeNameList([MMD_UpperLegLeft[0], MMD_UpperLegRight[0]])
    MMD_Root.pos = MMD_Root.pos + (GOH_FullBodyAlignmentPos - MMD_FullBodyAlignmentPos)

    #### Add Scale = 1 To tail, to match the Y Factor.
    Z_ScalingWeightByStep.pop(0)
    Z_ScalingWeightByStep.append(1/Z_ScalingFactor)

    ### This scale should be opreated in WORLD
    coordsys = getattr(pymxs.runtime, '%coordsys_context')
    prev_coordsys = coordsys(pymxs.runtime.Name('world'), None)
    ### Scaling
    for ScalingBone, Z_ScalingWeight, CurrentStepScaling_Y in zip(ScalingBones, Z_ScalingWeightByStep, Y_ScalingByStep):
        CurrentStepScaling_Z = Z_ScalingWeight * Z_ScalingFactor
        for CurrentBone in CurrentStepStartBones:
            rt.scale(GetNodeByNameRaiser(CurrentBone), rt.Point3(((CurrentStepScaling_Y * CurrentStepScaling_Z) ** 0.25), CurrentStepScaling_Y, CurrentStepScaling_Z))
    #### Also apply Last scaling on Neck
    UpperBody_LastStepScalingY = Y_ScalingByStep[-1]
    UpperBody_LastStepScalingZ = Z_ScalingWeightByStep[-1] * Z_ScalingFactor
    UpperBody_LastStepScalingX = (UpperBody_LastStepScalingY * UpperBody_LastStepScalingZ) ** 0.25
    rt.scale(GetNodeByNameRaiser(MMD_NeckBoneName), rt.Point3(UpperBody_LastStepScalingX, UpperBody_LastStepScalingY, UpperBody_LastStepScalingZ))
    # Restore previous coord
    coordsys(prev_coordsys, None)

    ### Distribute Upper body offset
    ### Distribute offset
    GOH_UpperBodyTargetList_With_Neck = GOH_UpperBodyTargetList + [GOH_NeckBoneName, GOH_NeckBoneName]
    MMD_UpperBodyTargetList_With_Neck = MMD_UpperBodyChain[-1] + [MMD_NeckBoneName, MMD_NeckBoneName]
    UpperBodyWithNeckOffset = GetMeanPosFromNodeNameList(GOH_UpperBodyTargetList_With_Neck) - GetMeanPosFromNodeNameList(MMD_UpperBodyTargetList_With_Neck)

    #### Decrease last step weight for offset
    LastStepOffsetWeightRatio = 0.25
    UpperBodyStepOffsetWeightSum = 0
    UpperBodyStepOffsetWeight = list()
    for CurrentStepStartBones, CurrentStepEndBones, CurrentStepWeightRaw in UpperBodySteps:
        UpperBodyStepOffsetWeightSum += CurrentStepWeightRaw
        UpperBodyStepOffsetWeight.append(CurrentStepWeightRaw)
    UpperBodyStepOffsetWeightSum -= UpperBodyStepOffsetWeight[-1] * (1-LastStepOffsetWeightRatio)
    UpperBodyStepOffsetWeight[-1] = UpperBodyStepOffsetWeight[-1] * LastStepOffsetWeightRatio


    for (CurrentStepStartBones, CurrentStepEndBones, CurrentStepWeightRaw), CurrentStepWeightOffset in zip(UpperBodySteps, UpperBodyStepOffsetWeight):
        CurrentStepWeight = CurrentStepWeightOffset / UpperBodyStepOffsetWeightSum
        for CurrentBoneName in CurrentStepEndBones:
            CurrentBone = GetNodeByNameRaiser(CurrentBoneName)
            CurrentBone.pos = CurrentBone.pos + (UpperBodyWithNeckOffset * CurrentStepWeight)

    ### Apply Final offset
    UpperBodyOffsetCollected = GetMeanPosFromNodeNameList(GOH_UpperBodyTargetList) - GetMeanPosFromNodeNameList(MMD_UpperBodyChain[-1])
    for CurrentBoneName in MMD_UpperBodyChain[-1]:
        CurrentBone = GetNodeByNameRaiser(CurrentBoneName)
        CurrentBone.pos = CurrentBone.pos + UpperBodyOffsetCollected
    #### Also Apply to neck
    GetNodeByNameRaiser(MMD_NeckBoneName).pos = GetNodeByNameRaiser(GOH_NeckBoneName).pos

    #### Normalize the scale and break linking before sizing for shoulder, legs and neck
    for CurrentBone in [MMD_ShoulderLeftName, MMD_ShoulderRightName, MMD_NeckBoneName, MMD_UpperLegLeft[0], MMD_UpperLegRight[0], MMD_UpperLegDLeft[0], MMD_UpperLegDRight[0]]:
        NormalizeScaleBreakLink(CurrentBone)
    
    #### Apply Final Offset to shoulders
    GetNodeByNameRaiser(MMD_ShoulderLeftName).pos = GetNodeByNameRaiser(GOH_ShoulderLeftName).pos
    GetNodeByNameRaiser(MMD_ShoulderRightName).pos = GetNodeByNameRaiser(GOH_ShoulderRightName).pos
    
    #### Get UpperBody / LowerBody Scale Ratio
    UpperBodyFittingFactor = 0.375
    LowerBodyFittingFactor = 0.25

    UpperBodyScaling = GetMeanScale(MMD_NeckBoneName)
    LowerBodyScaling = GetMeanScale(MMD_UpperLegLeft[0])

    Upper_Lower_Ratio = UpperBodyScaling / LowerBodyScaling
    UpperBodyFittingScaling = (1/Upper_Lower_Ratio) ** UpperBodyFittingFactor
    LowerBodyFittingScaling = (Upper_Lower_Ratio) ** LowerBodyFittingFactor
    
    for CurrentBoneName in [MMD_ShoulderLeftName, MMD_ShoulderRightName, MMD_NeckBoneName]:
        rt.scale(GetNodeByNameRaiser(CurrentBoneName), rt.Point3(UpperBodyFittingScaling, UpperBodyFittingScaling, UpperBodyFittingScaling))
    
    for CurrentBoneName in [MMD_UpperLegLeft[0], MMD_UpperLegRight[0], MMD_UpperLegDLeft[0], MMD_UpperLegDRight[0]]:
        rt.scale(GetNodeByNameRaiser(CurrentBoneName), rt.Point3(LowerBodyFittingScaling, LowerBodyFittingScaling, LowerBodyFittingScaling))

    LegLROffset = GetMeanPosFromNodeNameList([MMD_UpperLegRight[0], MMD_UpperLegDRight[0]]) - GetMeanPosFromNodeNameList([MMD_UpperLegLeft[0], MMD_UpperLegDLeft[0]])
    LegLRFittingOffset = (LegLROffset * (1-LowerBodyFittingScaling)) / 2.0
    GetNodeByNameRaiser(MMD_UpperLegLeft[0]).pos = GetNodeByNameRaiser(MMD_UpperLegLeft[0]).pos + LegLRFittingOffset
    GetNodeByNameRaiser(MMD_UpperLegDLeft[0]).pos = GetNodeByNameRaiser(MMD_UpperLegDLeft[0]).pos + LegLRFittingOffset
    GetNodeByNameRaiser(MMD_UpperLegRight[0]).pos = GetNodeByNameRaiser(MMD_UpperLegRight[0]).pos - LegLRFittingOffset
    GetNodeByNameRaiser(MMD_UpperLegDRight[0]).pos = GetNodeByNameRaiser(MMD_UpperLegDRight[0]).pos - LegLRFittingOffset

    ### Lower body alignment
    #### UpperLeg: Scaling Y -> Rotation YZ -> Rotation XZ
    #### UpperLeg Scaling
    AlignBoneLength(MMD_UpperLegLeft, GOH_UpperLegLeft, UpperLegScalingAxis)
    AlignBoneLength(MMD_UpperLegRight, GOH_UpperLegRight, UpperLegScalingAxis)
    AlignBoneLength(MMD_UpperLegDLeft, GOH_UpperLegLeft, UpperLegScalingAxis)
    AlignBoneLength(MMD_UpperLegDRight, GOH_UpperLegRight, UpperLegScalingAxis)

    #### LowerLeg: Scaling Y -> Rotation YZ -> Rotation XZ
    #### LowerLeg Scaling
    LowerLegExpectedHeight = GetMeanPosFromNodeNameList([MMD_LowerLegLeft[0], MMD_LowerLegRight[0], MMD_LowerLegDLeft[0], MMD_LowerLegDRight[0]]).z
    LowerLegCurrentHeight = LowerLegExpectedHeight - MMD_Mesh.min.z
    LowerLegScaling = LowerLegExpectedHeight / LowerLegCurrentHeight
    for CurrentBoneName in [MMD_LowerLegLeft[0], MMD_LowerLegRight[0], MMD_LowerLegDLeft[0], MMD_LowerLegDRight[0]]:
        rt.scale(GetNodeByNameRaiser(CurrentBoneName), rt.Point3(LowerLegScaling**0.5, LowerLegScaling**0.5, LowerLegScaling))

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

    ## Normalize Foot Scale
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
    GOH_LowerArmLeft_LengthOnly =  ("GFA_MWT_SKE_Hand2L", "GFA_MWT_SKE_Palm4L_hide")
    GOH_LowerArmRight = ("GFA_MWT_SKE_Hand2R", "GFA_MWT_SKE_Hand_rot1R")
    GOH_LowerArmRight_LengthOnly = ("GFA_MWT_SKE_Hand2R", "GFA_MWT_SKE_Palm3R") # The Original model Is ***King not symmetrical!!!!!!
    

    MMD_LowerArmLeft = ("Elbow_L", "Wrist_L")
    MMD_LowerArmLeft_LengthOnly =  ("Elbow_L", "MiddleFinger2_L")
    MMD_LowerArmRight = ("Elbow_R", "Wrist_R")
    MMD_LowerArmRight_LengthOnly = ("Elbow_R", "MiddleFinger2_R") # The Original model Is ***King not symmetrical!!!!!!

    LowerArmScalingAxis = "Y"

    ## LowerArm: Scaling Y -> Rotation YZ -> Rotation XZ
    ### LowerArm Scaling
    AlignBoneLength(MMD_LowerArmLeft_LengthOnly, GOH_LowerArmLeft_LengthOnly, LowerArmScalingAxis)
    AlignBoneLength(MMD_LowerArmRight_LengthOnly, GOH_LowerArmRight_LengthOnly, LowerArmScalingAxis)

    ### LowerArm Rotation (YZ -> XZ)
    AlignBoneRotationOnPlane(MMD_LowerArmLeft, GOH_LowerArmLeft, "YZ")
    AlignBoneRotationOnPlane(MMD_LowerArmLeft, GOH_LowerArmLeft, "XY")

    AlignBoneRotationOnPlane(MMD_LowerArmLeft, GOH_LowerArmLeft, "YZ")
    AlignBoneRotationOnPlane(MMD_LowerArmLeft, GOH_LowerArmLeft, "XY")

    AlignBoneRotationOnPlane(MMD_LowerArmRight, GOH_LowerArmRight, "YZ")
    AlignBoneRotationOnPlane(MMD_LowerArmRight, GOH_LowerArmRight, "XY")

    AlignBoneRotationOnPlane(MMD_LowerArmRight, GOH_LowerArmRight, "YZ")
    AlignBoneRotationOnPlane(MMD_LowerArmRight, GOH_LowerArmRight, "XY")
    # # Arm Further Fixing
    if MMD_Source_Config == "GF2":
        ApplyRotationOnPlane(GetNodeByNameRaiser(MMD_UpperArmLeft[0]), 1.25, "YZ")
        ApplyRotationOnPlane(GetNodeByNameRaiser(MMD_UpperArmRight[0]), -1.25, "YZ")

    # # Head Further Fixing
    if MMD_Source_Config == "GF2":
        # 0.875
        rt.scale(GetNodeByNameRaiser(MMD_NeckBoneName), rt.Point3(0.925, 0.925, 0.925))
        HeadBonePos = GetNodeByNameRaiser(MMD_HeadBoneName).pos
        NeckBonePos = GetNodeByNameRaiser(MMD_NeckBoneName).pos
        GetNodeByNameRaiser(MMD_HeadBoneName).pos = NeckBonePos + ((HeadBonePos - NeckBonePos) * 0.85)


    ### Normalize Hand scale
    NormalizeScaleBreakLink("Wrist_L")
    NormalizeScaleBreakLink("Wrist_R")
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


    # Align Thumb
    if MMD_Source_Config == "GF2":
        GOH_ThumbRotation = 20
        LeftThumbPointingAxis = ["+", "X"]
        RightThumbPointingAxis = ["+", "X"]
        ThumbRotatingTargetAxis = ["-", "Z"]
        AutoRotateFinger([MMD_Thumb_L1[0], MMD_Thumb_L2[0], MMD_Thumb_L2[1],], LeftThumbPointingAxis, ThumbRotatingTargetAxis, GOH_ThumbRotation)
        AutoRotateFinger([MMD_Thumb_R1[0], MMD_Thumb_R2[0], MMD_Thumb_R2[1],], RightThumbPointingAxis, ThumbRotatingTargetAxis, GOH_ThumbRotation)

    GOH_FingerRotation = 40 # ?
    ### Align and rotate other fingers.
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

    LeftHandPointingAxis = ["+", "Y"]
    RightHandPointingAxis = ["-", "Y"]
    RotatingTargetAxis = ["-", "Z"]
    AutoRotateFinger([MMD_IndexFinger_L1[0], MMD_IndexFinger_L2[0], MMD_IndexFinger_L2[1],], LeftHandPointingAxis, RotatingTargetAxis, GOH_FingerRotation)
    AutoRotateFinger([MMD_MiddleFinger_L1[0], MMD_MiddleFinger_L2[0], MMD_MiddleFinger_L2[1],], LeftHandPointingAxis, RotatingTargetAxis, GOH_FingerRotation)
    AutoRotateFinger([MMD_LittleFinger_L1[0], MMD_LittleFinger_L2[0], MMD_LittleFinger_L2[1],], LeftHandPointingAxis, RotatingTargetAxis, GOH_FingerRotation)
    AutoRotateFinger([MMD_RingFinger_L1[0], MMD_RingFinger_L2[0], MMD_RingFinger_L2[1],], LeftHandPointingAxis, RotatingTargetAxis, GOH_FingerRotation)

    AutoRotateFinger([MMD_IndexFinger_R1[0], MMD_IndexFinger_R2[0], MMD_IndexFinger_R2[1],], RightHandPointingAxis, RotatingTargetAxis, GOH_FingerRotation)
    AutoRotateFinger([MMD_MiddleFinger_R1[0], MMD_MiddleFinger_R2[0], MMD_MiddleFinger_R2[1],], RightHandPointingAxis, RotatingTargetAxis, GOH_FingerRotation)
    AutoRotateFinger([MMD_LittleFinger_R1[0], MMD_LittleFinger_R2[0], MMD_LittleFinger_R2[1],], RightHandPointingAxis, RotatingTargetAxis, GOH_FingerRotation)
    AutoRotateFinger([MMD_RingFinger_R1[0], MMD_RingFinger_R2[0], MMD_RingFinger_R2[1],], RightHandPointingAxis, RotatingTargetAxis, GOH_FingerRotation)

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
