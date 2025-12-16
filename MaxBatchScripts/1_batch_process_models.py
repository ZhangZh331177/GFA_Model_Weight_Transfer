import os
import json
import re
import pymxs

# ================= 配置区域 =================
# 输入目录 (包含 FBX 和 JSON 的根目录)
input_dir = r"E:\0_Self_Documents\Other\GOHMOD\maxscript\blender_output\z_shandian"
# ===========================================

rt = pymxs.runtime

def parse_max_color_string(color_str):
    """
    解析类似 "<Color (r=0.0000, g=0.0000, b=0.0000)>" 的字符串
    返回 3ds Max 的 color 对象
    """
    matches = re.findall(r"[-+]?\d*\.\d+|\d+", color_str)
    
    if len(matches) >= 3:
        r = float(matches[0]) * 255.0
        g = float(matches[1]) * 255.0
        b = float(matches[2]) * 255.0
        return rt.color(r, g, b)
    return rt.color(0, 0, 0)

def apply_material_from_json(json_path):
    """
    根据 JSON 文件创建并应用材质
    (逻辑源自 mesh_in_max.py，稍作修改以适应函数调用)
    """
    if not os.path.exists(json_path):
        print("错误: 找不到材质 JSON 文件: " + json_path)
        return

    try:
        with open(json_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        print("读取 JSON 失败: " + str(e))
        return

    for mesh_name, materials_map in data.items():
        try:
            print("正在处理材质对应模型: " + str(mesh_name))
        except:
            pass
        
        # 1. 创建多维子材质
        max_id = 0
        for mid in materials_map.keys():
            if int(mid) > max_id:
                max_id = int(mid)
        
        multi_mat = rt.Multimaterial(numsubs=(max_id + 1))
        # 尝试设置材质名
        try:
            multi_mat.name = mesh_name + "_Mat"
        except:
            multi_mat.name = "Imported_Mat"
        
        # 2. 创建子材质
        for mat_id_str, mat_data in materials_map.items():
            idx = int(mat_id_str)
            props = mat_data.get("Props", {})
            textures = mat_data.get("textures", {})
            
            sub_mat = rt.StandardMaterial()
            # 材质名处理
            mat_name = props.get("name", "SubMat_" + mat_id_str)
            # 避免编码问题导致赋值失败
            if isinstance(mat_name, unicode):
                # 尝试转码或保留
                try:
                    sub_mat.name = mat_name
                except:
                    sub_mat.name = "SubMat_" + mat_id_str
            else:
                sub_mat.name = str(mat_name)
            
            # 颜色
            diff_color_list = props.get("diffuse_color", [1,1,1,1])
            sub_mat.diffuse = rt.color(diff_color_list[0]*255, diff_color_list[1]*255, diff_color_list[2]*255)
            
            # 高光
            spec_str = props.get("specular_color", "")
            if spec_str:
                sub_mat.specular = parse_max_color_string(spec_str)
            
            # 粗糙度/光泽度
            roughness = props.get("roughness", 0.5)
            sub_mat.glossiness = (1.0 - roughness) * 100.0
            sub_mat.specularLevel = props.get("specular_intensity", 0.0) * 100.0

            # 贴图
            tex_path = textures.get("mmd_base_tex", "")
            if tex_path and os.path.exists(tex_path):
                bitmap_tex = rt.Bitmaptexture(fileName=tex_path)
                sub_mat.diffuseMap = bitmap_tex
                sub_mat.diffuseMapEnable = True
                rt.showTextureMap(sub_mat, bitmap_tex, True)
            
            # 透明度
            if diff_color_list[3] < 1.0:
                 sub_mat.opacity = diff_color_list[3] * 100.0

            multi_mat.materialList[idx] = sub_mat
            multi_mat.mapEnabled[idx] = True

        # 3. 赋材质
        target_obj = rt.getNodeByName(mesh_name)
        if target_obj:
            target_obj.material = multi_mat
            print("材质已应用。")
        else:
            print("警告: 场景中未找到名为 " + str(mesh_name) + " 的对象。")
            # 尝试模糊匹配 (有时候导入后名字可能会变)
            # 例如 "MeshName" 变成了 "MeshName001"
            # 这里简单尝试一下，如果不需要可以注释掉
            # for obj in rt.objects:
            #     if mesh_name in obj.name:
            #         obj.material = multi_mat
            #         break

def delete_all_keys():
    """
    删除场景中所有物体的所有动画关键帧
    """
    for obj in rt.objects:
        try:
            # deleteKeys <controller> #allKeys
            # 如果物体有控制器，删除其所有关键帧
            if obj.controller:
                rt.deleteKeys(obj.controller, rt.Name("allKeys"))
        except:
            pass

def process_fbx_files():
    if not os.path.exists(input_dir):
        print("目录不存在: " + input_dir)
        return

    print("开始扫描目录: " + input_dir)
    
    for root, dirs, files in os.walk(input_dir):
        for filename in files:
            # 检查是否为 _model.fbx
            if filename.lower().endswith("_model.fbx"):
                fbx_full_path = os.path.join(root, filename)
                base_name_no_ext = os.path.splitext(filename)[0] # e.g. "Char_model"
                
                # 提取核心名称: 去掉结尾的 "_model"
                # "Char_model" -> "Char"
                if base_name_no_ext.lower().endswith("_model"):
                    core_name = base_name_no_ext[:-6]
                else:
                    core_name = base_name_no_ext 
                
                print("=========================================")
                print("发现目标文件: " + filename)
                print("正在处理...")

                # 1. 重置 Max 场景 (不保存)
                # #noPrompt 禁止弹出确认框
                rt.resetMaxFile(rt.Name("noPrompt"))
                
                # 2. 导入 FBX
                # 使用 importFile，参数 #noPrompt 禁止弹窗
                try:
                    result = rt.importFile(fbx_full_path, rt.Name("noPrompt"))
                    if not result:
                        print("导入 FBX 失败 (返回 False): " + fbx_full_path)
                        # 即使失败也尝试继续，或者跳过
                        # continue 
                except Exception as e:
                    print("导入过程发生异常 (已忽略): " + str(e))

                # 2.5 删除所有关键帧
                print("正在清理所有动画关键帧...")
                delete_all_keys()

                # 3. 寻找并应用材质 JSON
                # 规则: 同目录下，后缀为 _Mat.json，且前缀匹配
                # 期望的 json 名: core_name + "_Mat.json"
                target_json_name = core_name + "_Mat.json"
                json_full_path = os.path.join(root, target_json_name)
                
                if os.path.exists(json_full_path):
                    print("找到匹配的材质文件: " + target_json_name)
                    apply_material_from_json(json_full_path)
                else:
                    print("未找到匹配的材质文件: " + target_json_name)
                
                # 4. 保存为 .max 文件
                # 名字后缀改为 "_Base.max" -> core_name + "_Base.max"
                # 或者按照题目要求: "该fbx不含后缀_model的部分" + "_Base.max" 
                # 其实就是 core_name + "_Base.max"
                
                # save_name = core_name + "_Base.max"
                # 题目原文："该fbx所在文件夹中寻找... 名字后缀改为"_Base""
                # 假设源文件是 "A_model.fbx"，生成 "A_Base.max"
                
                save_name = core_name + "_Base.max"
                save_full_path = os.path.join(root, save_name)
                
                try:
                    rt.saveMaxFile(save_full_path, clearNeedSaveFlag=True, useNewFile=True, quiet=True)
                    print("已保存工程文件: " + save_full_path)
                except Exception as e:
                    print("保存文件失败: " + str(e))

    print("=========================================")
    print("批量处理完成。")

# 执行
process_fbx_files()

