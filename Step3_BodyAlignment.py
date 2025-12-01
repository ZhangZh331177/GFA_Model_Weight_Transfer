from pymxs import runtime as rt

def GetPosFromNodeName(InputNodeName):
    return rt.getNodeByName(InputNodeName).pos

def GetMeanPoseFromNodeNameList(InputNodeNameList):
    NodePosList = list()
    for NodeName in InputNodeNameList:
        NodePosList.append(GetPosFromNodeName(NodeName))
    return sum(NodePosList) / len(NodePosList)

# We assume that both models are facing X+ (Right), and Head up to Z+ (UP), with foot contact the ground (Z=0)

# Parameter
MMD_RootName = "GirlsFrontline AlvaDefault"
MMD_Root = rt.getNodeByName(MMD_RootName)

# These Names SHOULD be fixed in different run

## Bones used to overall resize
GOH_Clavicle_Name_List = ["GFA_MWT_SKE_Clavicle_left", "GFA_MWT_SKE_Clavicle_right"]
MMD_Clavicle_Name_List = ["ShoulderP_L", "ShoulderP_R"]

## Bone used to overall align
GOH_UpperLeg_Name_List = ["GFA_MWT_SKE_foot1L", "GFA_MWT_SKE_foot1R"]
MMD_UpperLeg_Name_List = ["Leg_L", "Leg_R"]

# Overall Model Alignment
## Resize the model by clavicle height
GOH_Clavicle_Height = GetMeanPoseFromNodeNameList(GOH_Clavicle_Name_List).z
MMD_Clavicle_Height = GetMeanPoseFromNodeNameList(MMD_Clavicle_Name_List).z
MMD_Root.scale = MMD_Root.scale * (GOH_Clavicle_Height / MMD_Clavicle_Height)

## Align the model by hip (Use the center of two leg joints, do not directly use hip!)
GOH_HIP_Pose = GetMeanPoseFromNodeNameList(GOH_UpperLeg_Name_List)
MMD_HIP_Pose = GetMeanPoseFromNodeNameList(MMD_UpperLeg_Name_List)
MMD_Root.pos = MMD_Root.pos + (GOH_HIP_Pose - MMD_HIP_Pose)
