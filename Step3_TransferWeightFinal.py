from pymxs import runtime as rt

# Merge bone array
bone_merging_list = [
    [["ControlNode"], [("GFA_MWT_SKE_Body", 1.0)]],
    [["ParentNode"], [("GFA_MWT_SKE_Body", 1.0)]],
    [["Center"], [("GFA_MWT_SKE_Body", 1.0)]],
    [["Groove"], [("GFA_MWT_SKE_Body", 1.0)]],
    [["_shadow_WaistCancel_L"], [("GFA_MWT_SKE_Body", 1.0)]],
    [["_shadow_WaistCancel_R"], [("GFA_MWT_SKE_Body", 1.0)]],

    [["Waist"], [("GFA_MWT_SKE_Body", 1.0)]],

    [["LowerBody"], [("GFA_MWT_SKE_Body", 1.0)]],

    [["WaistCancel_R"], [("GFA_MWT_SKE_foot1R", 1.0)]], # ??????
    [["Leg_R"], [("GFA_MWT_SKE_foot1R", 1.0)]],
    [["LegD_R"], [("GFA_MWT_SKE_foot1R", 1.0)]],
    [["Knee_R"], [("GFA_MWT_SKE_foot2R", 1.0)]],
    [["KneeD_R"], [("GFA_MWT_SKE_foot2R", 1.0)]],
    [["Ankle_R"], [("GFA_MWT_SKE_foot2R", 0.5), ("GFA_MWT_SKE_foot3R", 0.5)]],
    [["AnkleD_R"], [("GFA_MWT_SKE_foot2R", 0.5), ("GFA_MWT_SKE_foot3R", 0.5)]],
    # [["AnkleTip_R"], [("GFA_MWT_SKE_foot3R", 1.0)]],
    # [["LegTipEX_R"], [("GFA_MWT_SKE_foot3R", 1.0)]],

    [["WaistCancel_L"], [("GFA_MWT_SKE_foot1L", 1.0)]], # ??????
    [["Leg_L"], [("GFA_MWT_SKE_foot1L", 1.0)]],
    [["LegD_L"], [("GFA_MWT_SKE_foot1L", 1.0)]],
    [["Knee_L"], [("GFA_MWT_SKE_foot2L", 1.0)]],
    [["KneeD_L"], [("GFA_MWT_SKE_foot2L", 1.0)]],
    [["Ankle_L"], [("GFA_MWT_SKE_foot2L", 0.5), ("GFA_MWT_SKE_foot3L", 0.5)]],
    [["AnkleD_L"], [("GFA_MWT_SKE_foot2L", 0.5), ("GFA_MWT_SKE_foot3L", 0.5)]],
    # [["AnkleTip_L"], [("GFA_MWT_SKE_foot3L", 1.0)]],
    # [["LegTipEX_L"], [("GFA_MWT_SKE_foot3L", 1.0)]],


    [["UpperBody"], [("GFA_MWT_SKE_IK_LeftRight", 1.0)]],
    [["UpperBody2"], [("GFA_MWT_SKE_IK_UpDown", 1.0)]],


    [["ShoulderP_L"], [("GFA_MWT_SKE_Clavicle_left", 1.0)]],
    [["Shoulder_L"], [("GFA_MWT_SKE_Clavicle_left", 1.0)]],
    [["ShoulderP_R"], [("GFA_MWT_SKE_Clavicle_right", 1.0)]],
    [["Shoulder_R"], [("GFA_MWT_SKE_Clavicle_right", 1.0)]],

    [["ShoulderC_L"], [("GFA_MWT_SKE_Hand1L", 1.0)]],
    [["Arm_L"], [("GFA_MWT_SKE_Hand1L", 1.0)]],
    [["ArmTwist_L"], [("GFA_MWT_SKE_Hand1L", 1.0)]],
    [["ShoulderC_R"], [("GFA_MWT_SKE_Hand1R", 1.0)]],
    [["Arm_R"], [("GFA_MWT_SKE_Hand1R", 1.0)]],
    [["ArmTwist_R"], [("GFA_MWT_SKE_Hand1R", 1.0)]],

    [["Elbow_L"], [("GFA_MWT_SKE_Hand2L", 1.0)]],
    [["HandTwist_L"], [("GFA_MWT_SKE_Hand2L", 0.9), ("GFA_MWT_SKE_Palm1L", 0.1)]], # Is this correct???
    [["Elbow_R"], [("GFA_MWT_SKE_Hand2R", 1.0)]],
    [["HandTwist_R"], [("GFA_MWT_SKE_Hand2R", 0.9), ("GFA_MWT_SKE_Palm1R", 0.1)]], # Is this correct???

    [["Neck"], [("GFA_MWT_SKE_Head", 1.0)]],
    [["Head"], [("GFA_MWT_SKE_Head", 1.0)]],
    [["Eye_L"], [("GFA_MWT_SKE_Head", 1.0)]],
    [["Eye_R"], [("GFA_MWT_SKE_Head", 1.0)]],


    [["Wrist_L"], [("GFA_MWT_SKE_Palm1L", 0.85), ("GFA_MWT_SKE_Palm1L", 0.15)]], # Is this correct???
    [["Thumb0_L"], [("GFA_MWT_SKE_Palm1L", 0.95), ("GFA_MWT_SKE_Palm1L", 0.05)]],
    [["Thumb1_L"], [("GFA_MWT_SKE_Palm1L", 1.0)]],
    [["Thumb2_L"], [("GFA_MWT_SKE_Palm1L", 1.0)]],

    [["IndexFinger1_L"], [("GFA_MWT_SKE_Palm1L", 0.55), ("GFA_MWT_SKE_Palm1L", 0.45)]],
    [["LittleFinger1_L"], [("GFA_MWT_SKE_Palm1L", 0.55), ("GFA_MWT_SKE_Palm1L", 0.45)]],
    [["MiddleFinger1_L"], [("GFA_MWT_SKE_Palm1L", 0.55), ("GFA_MWT_SKE_Palm1L", 0.45)]],
    [["RingFinger1_L"], [("GFA_MWT_SKE_Palm1L", 0.55), ("GFA_MWT_SKE_Palm1L", 0.45)]],

    [["IndexFinger2_L"], [("GFA_MWT_SKE_Palm1L", 0.25), ("GFA_MWT_SKE_Palm2L", 0.7), ("GFA_MWT_SKE_Palm3L", 0.05)]],
    [["LittleFinger2_L"], [("GFA_MWT_SKE_Palm1L", 0.25), ("GFA_MWT_SKE_Palm2L", 0.7), ("GFA_MWT_SKE_Palm3L", 0.05)]],
    [["MiddleFinger2_L"], [("GFA_MWT_SKE_Palm1L", 0.25), ("GFA_MWT_SKE_Palm2L", 0.7), ("GFA_MWT_SKE_Palm3L", 0.05)]],
    [["RingFinger2_L"], [("GFA_MWT_SKE_Palm1L", 0.25), ("GFA_MWT_SKE_Palm2L", 0.7), ("GFA_MWT_SKE_Palm3L", 0.05)]],

    [["IndexFinger3_L"], [("GFA_MWT_SKE_Palm1L", 0.15), ("GFA_MWT_SKE_Palm2L", 0.35), ("GFA_MWT_SKE_Palm3L", 0.5)]],
    [["LittleFinger3_L"], [("GFA_MWT_SKE_Palm1L", 0.15), ("GFA_MWT_SKE_Palm2L", 0.35), ("GFA_MWT_SKE_Palm3L", 0.5)]],
    [["MiddleFinger3_L"], [("GFA_MWT_SKE_Palm1L", 0.15), ("GFA_MWT_SKE_Palm2L", 0.35), ("GFA_MWT_SKE_Palm3L", 0.5)]],
    [["RingFinger3_L"], [("GFA_MWT_SKE_Palm1L", 0.15), ("GFA_MWT_SKE_Palm2L", 0.35), ("GFA_MWT_SKE_Palm3L", 0.5)]],

    [["Wrist_R"], [("GFA_MWT_SKE_Palm1R", 0.85), ("GFA_MWT_SKE_Palm1R", 0.15)]], # Is this correct???
    [["Thumb0_R"], [("GFA_MWT_SKE_Palm1R", 0.95), ("GFA_MWT_SKE_Palm1R", 0.05)]],
    [["Thumb1_R"], [("GFA_MWT_SKE_Palm1R", 1.0)]],
    [["Thumb2_R"], [("GFA_MWT_SKE_Palm1R", 1.0)]],

    [["IndexFinger1_R"], [("GFA_MWT_SKE_Palm1R", 0.55), ("GFA_MWT_SKE_Palm1R", 0.45)]],
    [["LittleFinger1_R"], [("GFA_MWT_SKE_Palm1R", 0.55), ("GFA_MWT_SKE_Palm1R", 0.45)]],
    [["MiddleFinger1_R"], [("GFA_MWT_SKE_Palm1R", 0.55), ("GFA_MWT_SKE_Palm1R", 0.45)]],
    [["RingFinger1_R"], [("GFA_MWT_SKE_Palm1R", 0.55), ("GFA_MWT_SKE_Palm1R", 0.45)]],

    [["IndexFinger2_R"], [("GFA_MWT_SKE_Palm1R", 0.25), ("GFA_MWT_SKE_Palm2R", 0.7), ("GFA_MWT_SKE_Palm3R", 0.05)]],
    [["LittleFinger2_R"], [("GFA_MWT_SKE_Palm1R", 0.25), ("GFA_MWT_SKE_Palm2R", 0.7), ("GFA_MWT_SKE_Palm3R", 0.05)]],
    [["MiddleFinger2_R"], [("GFA_MWT_SKE_Palm1R", 0.25), ("GFA_MWT_SKE_Palm2R", 0.7), ("GFA_MWT_SKE_Palm3R", 0.05)]],
    [["RingFinger2_R"], [("GFA_MWT_SKE_Palm1R", 0.25), ("GFA_MWT_SKE_Palm2R", 0.7), ("GFA_MWT_SKE_Palm3R", 0.05)]],
    
    [["IndexFinger3_R"], [("GFA_MWT_SKE_Palm1R", 0.15), ("GFA_MWT_SKE_Palm2R", 0.35), ("GFA_MWT_SKE_Palm3R", 0.5)]],
    [["LittleFinger3_R"], [("GFA_MWT_SKE_Palm1R", 0.15), ("GFA_MWT_SKE_Palm2R", 0.35), ("GFA_MWT_SKE_Palm3R", 0.5)]],
    [["MiddleFinger3_R"], [("GFA_MWT_SKE_Palm1R", 0.15), ("GFA_MWT_SKE_Palm2R", 0.35), ("GFA_MWT_SKE_Palm3R", 0.5)]],
    [["RingFinger3_R"], [("GFA_MWT_SKE_Palm1R", 0.15), ("GFA_MWT_SKE_Palm2R", 0.35), ("GFA_MWT_SKE_Palm3R", 0.5)]],
    
]

bone_merging_dict = dict()
for source_group, target_group in bone_merging_list:
    for target_name in target_group:
        if rt.getNodeByName(target_name) == None:
            raise(NameError("Error: Target Bone '"+target_name+"' do not exist!"))
    for source_name in source_group:
        if rt.getNodeByName(source_name) == None:
            print("Warning: Source Bone '" + str(source_name) + "' does not exist in scene, will be skipped if encountered.")
            continue
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