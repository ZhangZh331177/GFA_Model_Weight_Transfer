import os
import re
import pymxs

# ================= 配置区域 =================
# 输入目录
input_dir = r"E:\0_Self_Documents\Other\GOHMOD\mmd_model\4_test\20251223Simon"
# ===========================================

rt = pymxs.runtime

def is_invalid_name(s):
    """
    判断材质名是否包含非法字符。
    仅保留: 英文字母(a-z, A-Z), 数字(0-9), 下划线(_), 点(.)
    """
    if not s:
        return False
        
    valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.")
    
    for char in s:
        if char not in valid_chars:
            return True
    return False

def process_material_recursive(mtl, counter_ref, processed_handles):
    """
    递归遍历材质树，检查并重命名包含非ASCII字符的材质
    """
    if not mtl:
        return False

    # 尝试使用句柄来避免循环引用或重复处理
    # 如果 pymxs 版本支持 python 对象比较也可以，但句柄更稳妥
    try:
        h = rt.GetHandleByAnim(mtl)
        if h in processed_handles:
            return False
        processed_handles.add(h)
    except:
        # 如果无法获取句柄，尝试直接用对象ID或跳过查重（有风险但通常可行）
        pass

    changed = False

    # 1. 检查当前材质名称
    try:
        curr_name = mtl.name
        if is_invalid_name(curr_name):
            new_name = "TEMP_MTL_{:03d}".format(counter_ref[0])
            # print("  [重命名] '{}' -> '{}'".format(curr_name, new_name))
            mtl.name = new_name
            counter_ref[0] += 1
            changed = True
    except Exception as e:
        print("  [错误] 访问或修改材质名称失败: " + str(e))

    # 2. 递归检查子材质
    # 使用通用的 GetNumSubMtls 接口，适用于 MultiMaterial 和 Standard 等带子材质的类型
    try:
        num_subs = rt.getNumSubMtls(mtl)
        for i in range(1, num_subs + 1):
            sub = rt.getSubMtl(mtl, i)
            if sub:
                if process_material_recursive(sub, counter_ref, processed_handles):
                    changed = True
    except Exception as e:
        print("  [警告] 遍历子材质失败: " + str(e))

    return changed

def perform_uv_weld(skin_obj):
    """
    执行UVW焊接与塌陷操作
    """
    print("  正在执行UVW焊接操作...")
    try:
        # 1. 切换到修改面板
        rt.execute("max modify mode")
        
        # 2. 取消所有选中，选中skin
        rt.clearSelection()
        rt.select(skin_obj)
        
        # 3. 尝试选中‘可编辑网格’ (Base Object)
        if rt.isValidNode(skin_obj):
            rt.modPanel.setCurrentObject(skin_obj.baseObject)
        
        # 4. 添加UVW展开修改器
        uvw_mod = rt.Unwrap_UVW()
        rt.modPanel.addModToSelection(uvw_mod)
        
        # 5. 选中UVW展开修改器
        # addModToSelection 后，它是当前对象
        uvw_mod = rt.modPanel.getCurrentObject()
        
        # 6. 选择“多边形” (Level 3)
        rt.subObjectLevel = 3
        
        # 7. 打开UV编辑器
        uvw_mod.edit()
        
        # 8. 全选
        num_faces = uvw_mod.numberPolygons()
        if num_faces > 0:
            # 构建BitArray字符串 (Python 2兼容格式化)
            # 使用双大括号转义
            bit_str = "#{{1..{}}}".format(num_faces)
            all_faces = rt.execute(bit_str)
            uvw_mod.selectPolygons(all_faces)
            
            # 9. 设定焊接阈值
            uvw_mod.setWeldThreshold(0.0001)
            
            # 10. 焊接
            uvw_mod.weldSelected()
            
        # 11. 塌陷到 (Collapse To)
        # 获取修改器在堆栈中的索引
        mod_index = rt.modPanel.getModifierIndex(skin_obj, uvw_mod)
        rt.maxOps.CollapseNodeTo(skin_obj, mod_index, True)
        
        print("  UVW焊接并塌陷完成。")
        return True
        
    except Exception as e:
        print("  [警告] UVW焊接操作失败: " + str(e))
        return False

def process_max_file(file_path):
    print("--------------------------------------------------")
    print("正在处理文件: " + os.path.basename(file_path))
    
    try:
        # 打开文件，quiet=True 避免弹窗
        rt.loadMaxFile(file_path, quiet=True)
    except Exception as e:
        print("无法载入文件: " + str(e))
        return

    # 查找名为 skin 的物体
    skin_obj = rt.getNodeByName("skin")
    if not skin_obj:
        print("  跳过: 未找到名为 'skin' 的物体")
        return

    # 执行 UVW 焊接
    is_uv_changed = perform_uv_weld(skin_obj)

    # 获取材质
    # 如果对象在塌陷中丢失引用（虽不常见），尝试重新获取
    if not rt.isValidNode(skin_obj):
        skin_obj = rt.getNodeByName("skin")

    root_mtl = skin_obj.material
    
    is_mtl_changed = False
    if root_mtl:
        # 初始化计数器（使用列表以支持引用传递）和已处理集合
        counter = [1]
        processed_handles = set()

        print("  开始检查材质名称...")
        is_mtl_changed = process_material_recursive(root_mtl, counter, processed_handles)
    else:
        print("  警告: 'skin' 物体未指定材质，跳过材质检查。")

    if is_mtl_changed or is_uv_changed:
        print("  检测到更改，正在保存...")
        try:
            rt.saveMaxFile(file_path, quiet=True)
            print("  文件已保存。")
        except Exception as e:
            print("  [错误] 保存文件失败: " + str(e))
    else:
        print("  无需更改。")

def main():
    if not os.path.exists(input_dir):
        print("错误: 输入目录不存在 -> " + input_dir)
        return

    print("开始扫描目录: " + input_dir)
    found_count = 0
    
    for root, dirs, files in os.walk(input_dir):
        for filename in files:
            # 筛选后缀为 _final.max 或 _final_01.max 的文件（忽略大小写）
            if re.search(r'_final(_01)?\.max$', filename.lower()):
                full_path = os.path.join(root, filename)
                process_max_file(full_path)
                found_count += 1
                
                # 显式垃圾回收，防止批量处理时内存溢出
                rt.gc()

    print("==================================================")
    print("所有任务完成。共处理了 {} 个文件。".format(found_count))

if __name__ == "__main__":
    main()
