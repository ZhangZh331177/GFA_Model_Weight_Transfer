import os
import pymxs

# ================= 配置区域 =================
# 输入目录
input_dir = r"E:\0_Self_Documents\Other\GOHMOD\maxscript\blender_output\z_shandian"
# ===========================================

rt = pymxs.runtime

def has_non_ascii(s):
    """
    判断字符串是否包含非ASCII字符（即非英文、数字、基础符号）
    """
    if not s:
        return False
    for char in s:
        if ord(char) > 127:
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
        if has_non_ascii(curr_name):
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

    # 获取材质
    root_mtl = skin_obj.material
    if not root_mtl:
        print("  跳过: 'skin' 物体未指定材质")
        return

    # 初始化计数器（使用列表以支持引用传递）和已处理集合
    counter = [1]
    processed_handles = set()

    print("  开始检查材质名称...")
    is_changed = process_material_recursive(root_mtl, counter, processed_handles)

    if is_changed:
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
            # 筛选后缀为 _final.max 的文件（忽略大小写）
            if filename.lower().endswith("_final.max"):
                full_path = os.path.join(root, filename)
                process_max_file(full_path)
                found_count += 1
                
                # 显式垃圾回收，防止批量处理时内存溢出
                rt.gc()

    print("==================================================")
    print("所有任务完成。共处理了 {} 个文件。".format(found_count))

if __name__ == "__main__":
    main()
