from pymxs import runtime as rt

def IfInCoreBoneSet(InputBone):
    InputBoneName = InputBone.name
    CoreBoneSet = {"Waist","LowerBody","WaistCancel_L","Leg_L","Knee_L","Ankle_L","AnkleTip_L","LegD_L","KneeD_L","AnkleD_L","LegTipEX_L","WaistCancel_R","Leg_R","Knee_R","Ankle_R","AnkleTip_R","LegD_R","KneeD_R","AnkleD_R","LegTipEX_R",   "UpperBody","UpperBody2","ShoulderP_L","Shoulder_L","ShoulderC_L","Arm_L","ArmTwist_L","Elbow_L","HandTwist_L","Wrist_L","IndexFinger1_L","IndexFinger2_L","IndexFinger3_L","LittleFinger1_L","LittleFinger2_L","LittleFinger3_L","MiddleFinger1_L","MiddleFinger2_L","MiddleFinger3_L","RingFinger1_L","RingFinger2_L","RingFinger3_L","Thumb0_L","Thumb1_L","Thumb2_L","ShoulderP_R","Shoulder_R","ShoulderC_R","Arm_R","ArmTwist_R","Elbow_R","HandTwist_R","Wrist_R","IndexFinger1_R","IndexFinger2_R","IndexFinger3_R","LittleFinger1_R","LittleFinger2_R","LittleFinger3_R","MiddleFinger1_R","MiddleFinger2_R","MiddleFinger3_R","RingFinger1_R","RingFinger2_R","RingFinger3_R","Thumb0_R","Thumb1_R","Thumb2_R","Neck","Head","Eye_L","Eye_R",}
    return InputBoneName in CoreBoneSet

def RecursiveFindCoreBoneParentForObject(InputObject):
    CurrentParent = InputObject.parent
    if CurrentParent == None:
        return None
    elif IfInCoreBoneSet(CurrentParent):
        return CurrentParent
    else:
        return RecursiveFindCoreBoneParentForObject(CurrentParent)


def GetUnusedBoneCasting():
    CastingList = list()
    for currentObject in rt.objects:
        if IfInCoreBoneSet(currentObject):
            continue
        targetObject = RecursiveFindCoreBoneParentForObject(currentObject)
        if targetObject == None:
            continue
        else:
            CastingList.append(
                [[currentObject.name], [(targetObject.name, 1.0)]],
            )
    return CastingList

bone_merging_list = GetUnusedBoneCasting()

bone_names_set = set()
for source_bones, target_items in bone_merging_list:
    for bone_name in source_bones:
        bone_names_set.add(bone_name)
    for bone_name, bone_weight in target_items:
        bone_names_set.add(bone_name)
for bone_name in bone_names_set:
    if rt.getNodeByName(bone_name) == None:
        raise(NameError("Bone '"+bone_name+"' do not exist!"))


bone_merging_dict = dict()
for source_group, target_group in bone_merging_list:
    for source_name in source_group:
        bone_merging_dict[source_name] = target_group

body_mesh = rt.selection[0]
body_skin = body_mesh.skin
body_vert_count = body_mesh.numverts

# Generate Old Bone Set And Bone_ID-Bone_Name dict
old_bone_set = set()
bone_id2name_dict = dict()
current_bone_count = rt.skinOps.GetNumberBones(body_skin)
for i in range(1, current_bone_count + 1):
    bone_name = str(rt.skinOps.GetBoneName(body_skin, i, 0))
    old_bone_set.add(bone_name)
    bone_id2name_dict[i] = bone_name

# Save Source File Bone Weight
vertex_weight_input = list()
for vert_id in range(1, body_vert_count + 1):
    bone_weight_dict = dict()
    vert_bone_count = rt.skinOps.GetVertexWeightCount(body_skin, vert_id)
    for vert_bone_id in range(1, vert_bone_count + 1):
        bone_id = rt.skinOps.GetVertexWeightBoneID(body_skin, vert_id, vert_bone_id)
        bone_weight = rt.skinOps.GetVertexWeight(body_skin, vert_id, vert_bone_id)
        bone_weight_dict[bone_id2name_dict[bone_id]] = bone_weight
    vertex_weight_input.append(bone_weight_dict)

# Transfer_Weight
vertex_weight_transfer = dict()
current_vert_id = 1
for source_weight_dict in vertex_weight_input:
    bone_changed = False
    transfer_weight_dict = dict()
    for bone, weight in source_weight_dict.items():
        # Weight Transfered
        if bone in bone_merging_dict.keys():
            bone_changed = True
            target_bone_list = bone_merging_dict[bone]
            for target_bone, weight_ratio in target_bone_list:
                target_bone_weight = weight * weight_ratio
                # Weight Added
                if target_bone in transfer_weight_dict.keys():
                    transfer_weight_dict[target_bone] += target_bone_weight
                # Weight Created
                else:
                    transfer_weight_dict[target_bone] = target_bone_weight
        # Weight Not Transfered
        else:
            # Weight Added
            if bone in transfer_weight_dict.keys():
                transfer_weight_dict[bone] += weight
            # Weight Created
            else:
                transfer_weight_dict[bone] = weight
    if bone_changed:
        vertex_weight_transfer[current_vert_id] = transfer_weight_dict
    current_vert_id += 1

# Add New Bones To Skin
new_bone_set = set()
for source_bone, target_bone_list in bone_merging_dict.items():
    if source_bone in old_bone_set:
        for target_bone, weight_ratio in target_bone_list:
            if target_bone not in old_bone_set:
                new_bone_set.add(target_bone)
for new_bone_name in new_bone_set:
    new_bone = rt.getNodeByName(new_bone_name)
    rt.skinOps.AddBone(body_skin, new_bone, -1)

# Generate Bone_Name-Bone_ID dict
bone_name2id_dict = dict()
current_bone_count = rt.skinOps.GetNumberBones(body_skin)
for i in range(1, current_bone_count + 1):
    bone_name = str(rt.skinOps.GetBoneName(body_skin, i, 0))
    bone_name2id_dict[bone_name] = i

# Cast Weight To Mesh
for vert_id, bone_weight_dict in vertex_weight_transfer.items():
    bone_list = list()
    weight_list = list()
    for bone_name, bone_weight in bone_weight_dict.items():
        bone_list.append(bone_name2id_dict[bone_name])
        weight_list.append(bone_weight)
    rt.skinOps.ReplaceVertexWeights(body_skin,vert_id,bone_list,weight_list)

# Remove Merged Bones
for merging_bone_name in bone_merging_dict.keys():
    merging_bone = rt.getNodeByName(merging_bone_name)
    if merging_bone:
        merging_bone_childern_list = list(merging_bone.children)
        for child_node in merging_bone_childern_list:
            child_node.parent = merging_bone.parent
        rt.delete(merging_bone)