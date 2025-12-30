from pymxs import runtime as rt
import os

# ================= 配置区域 =================
# 输入目录
input_dir = r"E:\0_Self_Documents\Other\GOHMOD\mmd_model\4_test\20251223Simon"
template_file = r"E:\0_Self_Documents\Other\GOHMOD\mmd_model\template_renamed.max"
template_file_01 = r"E:\0_Self_Documents\Other\GOHMOD\mmd_model\test1225\TargetSkeleton_GAN01.max"
# ===========================================

# ==============================================================================
# 核心骨骼集合定义
# ==============================================================================
def get_core_bone_set():
    return {
        "Waist","LowerBody","WaistCancel_L","Leg_L","Knee_L","Ankle_L","AnkleTip_L",
        "LegD_L","KneeD_L","AnkleD_L","LegTipEX_L","WaistCancel_R","Leg_R","Knee_R",
        "Ankle_R","AnkleTip_R","LegD_R","KneeD_R","AnkleD_R","LegTipEX_R","UpperBody",
        "UpperBody2","ShoulderP_L","Shoulder_L","ShoulderC_L","Arm_L","ArmTwist_L",
        "Elbow_L","HandTwist_L","Wrist_L","IndexFinger1_L","IndexFinger2_L",
        "IndexFinger3_L","LittleFinger1_L","LittleFinger2_L","LittleFinger3_L",
        "MiddleFinger1_L","MiddleFinger2_L","MiddleFinger3_L","RingFinger1_L",
        "RingFinger2_L","RingFinger3_L","Thumb0_L","Thumb1_L","Thumb2_L","ShoulderP_R",
        "Shoulder_R","ShoulderC_R","Arm_R","ArmTwist_R","Elbow_R","HandTwist_R",
        "Wrist_R","IndexFinger1_R","IndexFinger2_R","IndexFinger3_R","LittleFinger1_R",
        "LittleFinger2_R","LittleFinger3_R","MiddleFinger1_R","MiddleFinger2_R",
        "MiddleFinger3_R","RingFinger1_R","RingFinger2_R","RingFinger3_R","Thumb0_R",
        "Thumb1_R","Thumb2_R","Neck","Head","Eye_L","Eye_R",
    }

def IfInCoreBoneSet(InputBone):
    return InputBone.name in get_core_bone_set()

def RecursiveFindCoreBoneParentForObject(InputObject):
    CurrentParent = InputObject.parent
    if CurrentParent == None:
        return None
    elif IfInCoreBoneSet(CurrentParent):
        return CurrentParent
    else:
        return RecursiveFindCoreBoneParentForObject(CurrentParent)

# ==============================================================================
# 模块 1: 重命名非 ASCII 对象
# ==============================================================================
def has_non_ascii(s):
    if isinstance(s, unicode):
        for char in s:
            if ord(char) > 127:
                return True
    else:
        try:
            s.decode('ascii')
        except UnicodeDecodeError:
            return True
    return False

def rename_non_english_objects():
    print("--- 开始重命名非 ASCII 对象 ---")
    step = 0
    all_objects = list(rt.objects)
    
    for currentObject in all_objects:
        obj_name = currentObject.name
        
        if has_non_ascii(obj_name):
            step += 1
            has_mesh_suffix = obj_name.lower().endswith("_mesh")
            new_base_name = "TEMPLATE_NAME_" + str(step)
            
            if has_mesh_suffix:
                currentObject.name = new_base_name + "_mesh"
            else:
                currentObject.name = new_base_name
            
            print("重命名完成: TEMPLATE_NAME_" + str(step))

# ==============================================================================
# 模块 2: 骨骼清理逻辑
# ==============================================================================
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

def execute_remove_unused_bones(body_mesh, body_skin):
    print("--- 开始执行无用骨骼移除与权重转移 ---")
    
    bone_merging_list = GetUnusedBoneCasting()
    
    bone_names_set = set()
    for source_bones, target_items in bone_merging_list:
        for bone_name in source_bones:
            bone_names_set.add(bone_name)
        for bone_name, bone_weight in target_items:
            bone_names_set.add(bone_name)
    
    for bone_name in bone_names_set:
        if rt.getNodeByName(bone_name) == None:
            print("警告: 骨骼 '" + bone_name + "' 不存在，跳过清理流程。")
            return

    bone_merging_dict = dict()
    for source_group, target_group in bone_merging_list:
        for source_name in source_group:
            bone_merging_dict[source_name] = target_group

    body_vert_count = rt.skinOps.GetNumberVertices(body_skin)
    # 使用 Skin 自身的顶点数，而不是 Mesh 的顶点数，以防 Modifier Stack 中有其他改变拓扑的修改器
    # body_vert_count = rt.skinOps.GetNumberVertices(body_skin)
    
    old_bone_set = set()
    bone_id2name_dict = dict()
    current_bone_count = rt.skinOps.GetNumberBones(body_skin)
    for i in range(1, current_bone_count + 1):
        bone_name = str(rt.skinOps.GetBoneName(body_skin, i, 0))
        old_bone_set.add(bone_name)
        bone_id2name_dict[i] = bone_name

    vertex_weight_input = list()
    for vert_id in range(1, body_vert_count + 1):
        bone_weight_dict = dict()
        vert_bone_count = rt.skinOps.GetVertexWeightCount(body_skin, vert_id)
        for vert_bone_id in range(1, vert_bone_count + 1):
            bone_id = rt.skinOps.GetVertexWeightBoneID(body_skin, vert_id, vert_bone_id)
            bone_weight = rt.skinOps.GetVertexWeight(body_skin, vert_id, vert_bone_id)
            if bone_id in bone_id2name_dict:
                bone_weight_dict[bone_id2name_dict[bone_id]] = bone_weight
        vertex_weight_input.append(bone_weight_dict)

    vertex_weight_transfer = dict()
    current_vert_id = 1
    for source_weight_dict in vertex_weight_input:
        bone_changed = False
        transfer_weight_dict = dict()
        for bone, weight in source_weight_dict.items():
            if bone in bone_merging_dict.keys():
                bone_changed = True
                target_bone_list = bone_merging_dict[bone]
                for target_bone, weight_ratio in target_bone_list:
                    target_bone_weight = weight * weight_ratio
                    if target_bone in transfer_weight_dict.keys():
                        transfer_weight_dict[target_bone] += target_bone_weight
                    else:
                        transfer_weight_dict[target_bone] = target_bone_weight
            else:
                if bone in transfer_weight_dict.keys():
                    transfer_weight_dict[bone] += weight
                else:
                    transfer_weight_dict[bone] = weight
        if bone_changed:
            vertex_weight_transfer[current_vert_id] = transfer_weight_dict
        current_vert_id += 1

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

    bone_name2id_dict = dict()
    current_bone_count = rt.skinOps.GetNumberBones(body_skin)
    for i in range(1, current_bone_count + 1):
        bone_name = str(rt.skinOps.GetBoneName(body_skin, i, 0))
        bone_name2id_dict[bone_name] = i

    rt.modPanel.setCurrentObject(body_skin)
    
    for vert_id, bone_weight_dict in vertex_weight_transfer.items():
        bone_list = list()
        weight_list = list()
        for bone_name, bone_weight in bone_weight_dict.items():
            if bone_name in bone_name2id_dict:
                bone_list.append(bone_name2id_dict[bone_name])
                weight_list.append(bone_weight)
        if len(bone_list) > 0:
            try:
                rt.skinOps.ReplaceVertexWeights(body_skin, vert_id, bone_list, weight_list)
            except Exception as e:
                print("Error replacing weights for Vert ID: {}, BoneList: {}, WeightList: {}".format(vert_id, bone_list, weight_list))
                raise e

    for merging_bone_name in bone_merging_dict.keys():
        merging_bone = rt.getNodeByName(merging_bone_name)
        if merging_bone:
            merging_bone_childern_list = list(merging_bone.children)
            for child_node in merging_bone_childern_list:
                child_node.parent = merging_bone.parent
            rt.delete(merging_bone)
    
    print("骨骼清理完成。")

# ==============================================================================
# 模块 3: 脖子缩放计算
# ==============================================================================
def VecDot(PointA, PointB):
    return (PointA.x * PointB.x) + (PointA.y * PointB.y) + (PointA.z * PointB.z)

def VecNorm(Point):
    return (Point.x ** 2 + Point.y ** 2 + Point.z ** 2) ** 0.5

def calculate_neck_scale_ratio():
    LeftEyeName = "Eye_L"
    RightEyeName = "Eye_R"
    NeckName = "Neck"
    LeftShoulderName = "ShoulderP_L"
    RightShoulderName = "ShoulderP_R"
    LeftFootName = "Ankle_L"
    RightFootName = "Ankle_R"

    # Check if bones exist
    required_bones = [LeftEyeName, RightEyeName, NeckName, LeftShoulderName, RightShoulderName, LeftFootName, RightFootName]
    for name in required_bones:
        if rt.getNodeByName(name) == None:
            print("计算脖子缩放跳过: 缺少骨骼 " + name)
            return None

    LeftEyePos = rt.getNodeByName(LeftEyeName).pos
    RightEyePos = rt.getNodeByName(RightEyeName).pos
    NeckPos = rt.getNodeByName(NeckName).pos
    LeftShoulderPos = rt.getNodeByName(LeftShoulderName).pos
    RightShoulderPos = rt.getNodeByName(RightShoulderName).pos
    LeftFootPos = rt.getNodeByName(LeftFootName).pos
    RightFootPos = rt.getNodeByName(RightFootName).pos

    #### Head size factors
    BodyVector = ((LeftShoulderPos + RightShoulderPos) - (LeftFootPos + RightFootPos)) / 2.0 #[0,-0.174142,-50.6248]
    BodyDistance = VecNorm(BodyVector) # 50.62509951077789
    
    if BodyDistance == 0:
         return None

    EyeLRVector = LeftEyePos - RightEyePos
    EyeLRDistance = VecNorm(EyeLRVector) # 2.11018
    EyeLRRatio = EyeLRDistance / BodyDistance
    EyeLRExpectedRatio = 0.041682486 # 2.11018 / 50.62509951077789
    
    if EyeLRRatio == 0:
        return None
        
    RatioOffsetByEyeLR = EyeLRExpectedRatio / EyeLRRatio

    EyeNeckVector = ((LeftEyePos + RightEyePos) / 2.0) - NeckPos #[0,-2.38843,5.42931]
    EyeNeckDistanceOnBodyDirection = abs(VecDot(EyeNeckVector, BodyVector)) / VecNorm(BodyVector) # 5.421062073221453
    EyeNeckRatio = EyeNeckDistanceOnBodyDirection / BodyDistance
    EyeNeckExpectedRatio = 0.1070825 # 5.421062073221453 / 50.62509951077789
    
    if EyeNeckRatio == 0:
        return None

    RatioOffsetByEyeNeck = EyeNeckExpectedRatio / EyeNeckRatio

    #### Resize Head
    RatioOffset = (RatioOffsetByEyeLR * RatioOffsetByEyeNeck) ** (1.0/2.0)
    return RatioOffset

# ==============================================================================
# 单场景处理流程
# ==============================================================================
def process_single_scene():
    # 0. 预先计算脖子缩放比例 (在清理骨骼之前，确保骨骼存在且位置正确)
    neck_scale_ratio = calculate_neck_scale_ratio()
    if neck_scale_ratio:
        print("已计算脖子缩放比例: {:.4f}".format(neck_scale_ratio))
    else:
        print("未能计算脖子缩放比例 (可能缺少参照骨骼)")

    # 1. 取消所有选中
    rt.clearSelection()

    # 2. 重命名非 ASCII 对象
    rename_non_english_objects()

    # 3. 取消所有选中
    rt.clearSelection()

    # 4. 查找后缀为 "_mesh" 的物体
    target_mesh = None
    for obj in rt.objects:
        try:
            if obj.name.lower().endswith("_mesh"):
                target_mesh = obj
                break # 只选中第一个
        except UnicodeDecodeError:
            continue
    
    skin_mod = None
    
    if target_mesh:
        try:
            print("选中目标网格: " + target_mesh.name)
        except:
            pass
        rt.select(target_mesh)
        
        # 5. 删除变形器
        modifiers_to_delete = []
        for mod in target_mesh.modifiers:
            if rt.classOf(mod) == rt.Morpher:
                modifiers_to_delete.append(mod)
        
        for mod in modifiers_to_delete:
            try:
                print("删除变形器: " + str(mod.name))
            except:
                pass
            rt.deleteModifier(target_mesh, mod)

        # 6. 操作蒙皮
        for mod in target_mesh.modifiers:
            if rt.classOf(mod) == rt.Skin:
                skin_mod = mod
                break
        
        if skin_mod:
            try:
                print("找到蒙皮修改器: " + str(skin_mod.name))
            except:
                pass
            
            rt.setCommandPanelTaskMode(rt.name("modify"))
            rt.modPanel.setCurrentObject(skin_mod)
            
            execute_remove_unused_bones(target_mesh, skin_mod)
        else:
            print("未找到蒙皮修改器，跳过骨骼清理。")
    else:
        print("未找到后缀为 '_mesh' 的物体。")

    # 7. 应用脖子缩放 (如果计算成功)
    if neck_scale_ratio:
        neck_node = rt.getNodeByName("Neck")
        if neck_node:
            print("应用脖子缩放: {:.4f}".format(neck_scale_ratio))
            try:
                # 使用 scale 函数应用缩放变换
                rt.scale(neck_node, rt.Point3(neck_scale_ratio, neck_scale_ratio, neck_scale_ratio))
            except Exception as e:
                print("应用脖子缩放失败: " + str(e))
        else:
            print("警告: Neck 骨骼在清理后未找到，无法应用缩放。")

    return target_mesh, skin_mod

# ==============================================================================
# 批量处理主流程
# ==============================================================================
def process_files():
    if not os.path.exists(input_dir):
        print("目录不存在: " + input_dir)
        return

    print("开始扫描目录: " + input_dir)
    
    for root, dirs, files in os.walk(input_dir):
        for filename in files:
            # 查找 _Base.max 文件
            if filename.lower().endswith("_base.max"):
                file_full_path = os.path.join(root, filename)
                print("=========================================")
                print("发现目标文件: " + filename)
                
                # 1. 打开文件 (不保存当前场景)
                # quiet=True 禁止弹窗
                try:
                    rt.loadMaxFile(file_full_path, quiet=True)
                except Exception as e:
                    print("打开文件失败: " + str(e))
                    continue

                # 2. 执行清理流程
                target_mesh, skin_mod = process_single_scene()
                
                # 3. 检查骨骼比例并保存
                should_save = False
                
                if target_mesh and skin_mod:
                    # 重新选中并激活蒙皮 (以防中间状态改变)
                    try:
                        rt.select(target_mesh)
                        rt.setCommandPanelTaskMode(rt.name("modify"))
                        rt.modPanel.setCurrentObject(skin_mod)
                        
                        # 统计骨骼
                        core_set = get_core_bone_set()
                        core_set_total = len(core_set)
                        
                        matched_count = 0
                        current_bone_count = rt.skinOps.GetNumberBones(skin_mod)
                        
                        # 遍历当前 Skin 中的所有骨骼
                        for i in range(1, current_bone_count + 1):
                            # 0 获取名字
                            bone_name = str(rt.skinOps.GetBoneName(skin_mod, i, 0))
                            if bone_name in core_set:
                                matched_count += 1
                        
                        if core_set_total > 0:
                            ratio = float(matched_count) / float(core_set_total)
                            print("CoreBoneSet 覆盖率: {:.2f}% ({}/{})".format(ratio * 100, matched_count, core_set_total))
                            
                            if ratio > 0.3:
                                should_save = True
                                print("覆盖率 > 30%，准备保存。")
                            else:
                                print("覆盖率 <= 30%，跳过保存。")
                        else:
                            print("CoreBoneSet 为空，跳过。")
                            
                    except Exception as e:
                        print("检查骨骼比例时出错: " + str(e))
                else:
                    print("未找到 Mesh 或 Skin，跳过保存。")

                # 4. 保存文件
                if should_save:
                    # 取消选中
                    rt.clearSelection()
                    
                    # 构造新文件名: _Base.max -> _Simplified.max
                    # 使用不区分大小写的替换
                    new_filename = re.sub(r'_base\.max$', '_Simplified.max', filename, flags=re.IGNORECASE)
                    save_full_path = os.path.join(root, new_filename)
                    
                    try:
                        rt.saveMaxFile(save_full_path, clearNeedSaveFlag=True, useNewFile=True, quiet=True)
                        print("已保存: " + new_filename)
                        
                        # =========================================================
                        # 流程 A: 合并模板并另存为 _Merged
                        # =========================================================
                        if os.path.exists(template_file):
                            print("正在合并模板文件: " + template_file)
                            
                            # 合并 Max 文件
                            # mergeMaxFile <filename> [ #mergeDups | #skipDups | #promptDups ] [ #deleteOldDups ] [ #select ] [ #promptReparent ] [ #alwaysReparent ] [ #neverReparent ] [ quiet:<bool> ]
                            # 使用 #mergeDups (如果有重名，自动合并/重命名，通常模板和角色骨骼可能重名，需要根据实际情况决定)
                            # 这里使用默认行为或者 #mergeDups
                            try:
                                rt.mergeMaxFile(template_file, rt.Name("mergeDups"), quiet=True)
                                
                                # 构造 _Merged 文件名
                                merged_filename = re.sub(r'_Simplified\.max$', '_Merged.max', new_filename, flags=re.IGNORECASE)
                                merged_full_path = os.path.join(root, merged_filename)
                                
                                rt.saveMaxFile(merged_full_path, clearNeedSaveFlag=True, useNewFile=True, quiet=True)
                                print("已保存合并版: " + merged_filename)
                                
                            except Exception as e:
                                print("合并模板失败: " + str(e))
                        else:
                            print("警告: 模板文件不存在: " + template_file)
                        
                        # =========================================================
                        # 流程 B: 合并模板 01 并另存为 _Merged_01
                        # =========================================================
                        # 检查 template_file_01 是否已定义
                        target_template_01 = None
                        if 'template_file_01' in globals():
                            target_template_01 = template_file_01
                        
                        if target_template_01 and os.path.exists(target_template_01):
                            print("正在合并模板文件 01: " + target_template_01)
                            
                            try:
                                # 关键：重新加载 _Simplified.max，清除之前可能合并过的 template_file，确保环境纯净
                                rt.loadMaxFile(save_full_path, quiet=True)
                                
                                rt.mergeMaxFile(target_template_01, rt.Name("mergeDups"), quiet=True)
                                
                                merged_01_filename = re.sub(r'_Simplified\.max$', '_Merged_01.max', new_filename, flags=re.IGNORECASE)
                                merged_01_full_path = os.path.join(root, merged_01_filename)
                                
                                rt.saveMaxFile(merged_01_full_path, clearNeedSaveFlag=True, useNewFile=True, quiet=True)
                                print("已保存合并版 01: " + merged_01_filename)
                                
                            except Exception as e:
                                print("合并模板 01 失败: " + str(e))
                        elif target_template_01:
                             print("警告: 模板文件 01 不存在: " + target_template_01)
                        # =========================================================
                        
                    except Exception as e:
                        print("保存文件失败: " + str(e))

    print("=========================================")
    print("批量处理完成。")

import re # 需要用到正则替换文件名后缀
if __name__ == "__main__":
    process_files()
