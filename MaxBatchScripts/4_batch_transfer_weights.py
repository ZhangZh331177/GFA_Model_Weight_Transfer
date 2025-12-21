import pymxs
from pymxs import runtime as rt
import os
import re

# ================= 配置区域 =================
# 输入目录 (参考 3_batch_align.py)
input_dir = r"E:\0_Self_Documents\Other\GOHMOD\mmd_model\2_temp\GF2tec"
# 通用前缀 (用于 safr_pack_6 字段)
SAFR_PREFIX = "agf_"
# ===========================================

def transfer_weights(body_mesh, body_skin):
    """
    执行 ref_3_3_TransferWeightFinal.py 的核心逻辑
    """
    print("开始执行权重转移逻辑...")
    
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
        [["AnkleTip_R"], [("GFA_MWT_SKE_foot2R", 1.0)]],
        [["LegTipEX_R"], [("GFA_MWT_SKE_foot3R", 1.0)]],

        [["WaistCancel_L"], [("GFA_MWT_SKE_foot1L", 1.0)]], # ??????
        [["Leg_L"], [("GFA_MWT_SKE_foot1L", 1.0)]],
        [["LegD_L"], [("GFA_MWT_SKE_foot1L", 1.0)]],
        [["Knee_L"], [("GFA_MWT_SKE_foot2L", 1.0)]],
        [["KneeD_L"], [("GFA_MWT_SKE_foot2L", 1.0)]],
        [["Ankle_L"], [("GFA_MWT_SKE_foot2L", 0.5), ("GFA_MWT_SKE_foot3L", 0.5)]],
        [["AnkleD_L"], [("GFA_MWT_SKE_foot2L", 0.5), ("GFA_MWT_SKE_foot3L", 0.5)]],
        [["AnkleTip_L"], [("GFA_MWT_SKE_foot2L", 1.0)]],
        [["LegTipEX_L"], [("GFA_MWT_SKE_foot3L", 1.0)]],


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
        

    # 使用传入的 body_mesh 和 body_skin
    # body_mesh = rt.selection[0] 
    # body_skin = body_mesh.skin
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
        if new_bone:
            rt.skinOps.AddBone(body_skin, new_bone, -1)
        else:
            print("Warning: Target bone '" + str(new_bone_name) + "' not found, cannot add to skin.")

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
            if bone_name in bone_name2id_dict:
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
    
    print("权重转移完成。")

def delete_hierarchy(node):
    """递归删除节点及其所有子节点"""
    if node:
        children = [c for c in node.children]
        for child in children:
            delete_hierarchy(child)
        rt.delete(node)

def process_files():
    if not os.path.exists(input_dir):
        print("目录不存在: " + input_dir)
        return

    print("开始扫描目录: " + input_dir)
    
    for root, dirs, files in os.walk(input_dir):
        for filename in files:
            # 寻找所有的 "_Aligned" 后缀的 max 文件
            if filename.lower().endswith("_aligned.max"):
                file_full_path = os.path.join(root, filename)
                print("=========================================")
                print("发现目标文件: " + filename)
                
                try:
                    # 打开（不保存之前内容）
                    rt.loadMaxFile(file_full_path, quiet=True)
                except Exception as e:
                    print("打开文件失败: " + str(e))
                    continue

                # 1. 识别 mmd_root_name (复用 3_batch_align.py 逻辑)
                root_nodes = [node for node in rt.objects if node.parent == None]
                mmd_root_name = None
                # mmd_mesh_name = None # 我们已经在下面重新查找了
                
                for node in root_nodes:
                    node_name = node.name
                    if node_name.lower().endswith("_mesh"):
                        pass # mmd_mesh_name = node_name
                    elif node_name.startswith("GFA_MWT_SKE_"):
                        pass
                    else:
                        mmd_root_name = node_name

                # 取消所有选中
                rt.clearSelection()

                # 选中其中以 "_mesh" 为后缀的物体（如果有多个选第一个）
                target_mesh = None
                for obj in rt.objects:
                    if obj.name.lower().endswith("_mesh"):
                        target_mesh = obj
                        break
                
                if not target_mesh:
                    print("未找到以 _mesh 结尾的物体，跳过此文件。")
                    continue
                
                # 检查其修改器中是否有蒙皮
                skin_mod = None
                for mod in target_mesh.modifiers:
                    if str(mod.classID) == "#(9815843, 87654)": # Skin ClassID
                         skin_mod = mod
                         break
                
                if not skin_mod:
                    if hasattr(target_mesh, "skin") and target_mesh.skin:
                        skin_mod = target_mesh.skin
                
                if not skin_mod:
                    print("物体 " + target_mesh.name + " 没有蒙皮修改器，跳过此文件。")
                    continue
                
                # 如果有，则选中修改器中的蒙皮
                rt.select(target_mesh)
                rt.modPanel.setCurrentObject(skin_mod)

                try:
                    # 在 Python 2 中直接打印 unicode 通常是可以的
                    print(u"找到目标物体: " + target_mesh.name)
                except:
                    print("找到目标物体 (名称包含特殊字符)")
                print("正在执行权重转移流程...")
                
                try:
                    transfer_weights(target_mesh, skin_mod)
                except Exception as e:
                    print("权重转移执行出错: " + str(e))
                    continue

                # =========================================================
                # 后处理步骤
                # =========================================================
                rt.clearSelection()

                # 1. 清理多余根节点
                # 逻辑：保留 mmd_mesh (target_mesh) 和 GFA_MWT_SKE_ 开头的节点，删除其他所有根节点
                root_nodes = [node for node in rt.objects if node.parent == None]
                
                for node in root_nodes:
                    # 如果是目标 mesh，保留
                    if node == target_mesh:
                        continue
                    
                    # 如果是 GFA 骨架相关，保留
                    if node.name.startswith("GFA_MWT_SKE_"):
                        continue
                    
                    # 其他的都要删除
                    try:
                        # 尝试打印名字
                        try:
                            print("删除多余根节点及其子层级: " + node.name)
                        except:
                            pass
                        delete_hierarchy(node)
                    except Exception as e:
                        print("删除节点失败: " + str(e))

                # 2. 删除名为“GFA_MWT_SKE_skin”的物体
                old_skin = rt.getNodeByName("GFA_MWT_SKE_skin")
                if old_skin:
                    rt.delete(old_skin)

                # 3. 将 target_mesh 重命名为“GFA_MWT_SKE_skin”
                target_mesh.name = "GFA_MWT_SKE_skin"

                # 4. 移动到“GFA_MWT_SKE_Basis”之下
                basis = rt.getNodeByName("GFA_MWT_SKE_Basis")
                if basis:
                    target_mesh.parent = basis
                    
                    # 5. 修改“GFA_MWT_SKE_Basis”的 User Prop "safr_pack_6"
                    folder_name = os.path.basename(root)
                    new_safr_val = SAFR_PREFIX + folder_name
                    
                    # rt.setUserProp(basis, "safr_pack_6", new_safr_val)
                    # 修改为直接替换字符串
                    current_buffer = rt.getUserPropBuffer(basis)
                    if "safr_pack_6" in current_buffer:
                        new_buffer = current_buffer.replace("safr_pack_6", new_safr_val)
                        rt.setUserPropBuffer(basis, new_buffer)
                else:
                    print("警告: 未找到 GFA_MWT_SKE_Basis，无法设置父级和属性。")

                # 6. 将“GFA_MWT_SKE_skin”的属性-用户定义清空，重写为"poly"
                rt.setUserPropBuffer(target_mesh, "poly")

                # 7. Name Avoidance (移除 Prefix)
                Prefix = "GFA_MWT_SKE_"
                for currentObject in rt.objects:
                    if currentObject.name.startswith(Prefix):
                        currentObject.name = currentObject.name[len(Prefix):]

                # 8. 另存为 _Final.max
                save_filename = re.sub(r'_Aligned\.max$', '_Final.max', filename, flags=re.IGNORECASE)
                save_full_path = os.path.join(root, save_filename)
                
                try:
                    rt.saveMaxFile(save_full_path, clearNeedSaveFlag=True, useNewFile=True, quiet=True)
                    print("已保存文件: " + save_filename)
                except Exception as e:
                    print("保存文件失败: " + str(e))

    print("=========================================")
    print("批量处理完成。")

if __name__ == "__main__":
    process_files()
