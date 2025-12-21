import bpy
from bpy_types import bpy_types
import os
import json
import time

def ensure_addon_enabled(addon_name):
    """Check and enable a specific addon if available."""    
    # Check if already enabled
    if addon_name in bpy.context.preferences.addons:
        return True
    
    # Try to enable it
    try:
        bpy.ops.preferences.addon_enable(module=addon_name)
        return True
    except Exception:
        return False
    
def reset_blender():
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)


def ImportMMDFile(InputPath):
    # Import file
    try:
        bpy.ops.mmd_tools.import_model(
            filepath=InputPath,
            types={'MESH', 'ARMATURE', 'PHYSICS', 'DISPLAY', 'MORPHS'},
            scale=0.08,
            clean_model=True,
            remove_doubles=False,
            fix_IK_links=False,
            # ik_loop_factor=5,
            apply_bone_fixed_axis=False,
            rename_bones=True,
            use_underscore=False,
            dictionary='INTERNAL',
            use_mipmap=True,
            sph_blend_factor=1.0,
            spa_blend_factor=1.0,
            log_level='WARNING',
            save_log=False
        )
        print(f"Successfully imported: {InputPath}")
    except Exception as e:
        print(f"Error importing MMD model: {e}")
        return False

def ExportDAEFile(OutputPath):
    try:
        bpy.ops.wm.collada_export(
            filepath=OutputPath,
            check_existing=False,
            
            apply_modifiers=True,
            triangulate=False, 

            export_global_forward_selection='Y',
            export_global_up_selection='Z',

            include_animations=False,

            keep_bind_info=True
            )
        print(f"Successfully exported: {OutputPath}")
        return True
    except Exception as e:
        print(f"Error exporting to DAE: {e}")
        return False

def HasParentOfName(InputObject, InputName):
    ParentObject = InputObject
    while ParentObject != None:
        if ParentObject.name == InputName:
            return True
        else:
            ParentObject = ParentObject.parent
    return False

def HasParentOfNameInSet(InputObject, InputNameSet):
    ParentObject = InputObject
    while ParentObject != None:
        if ParentObject.name in InputNameSet:
            return True
        else:
            ParentObject = ParentObject.parent
    return False

def IsJsonSerializable(obj) -> bool:
    try:
        json.dumps(obj)
        return True
    except (TypeError, OverflowError):
        return False

def MatToDict(mat):
    OutputDict = {}
    OutputDict["Props"] = dict()
    for prop in mat.bl_rna.properties:
        if not prop.is_readonly:
            try:
                value = getattr(mat, prop.identifier)
                # Convert Blender types to Python types
                if hasattr(value, 'to_list'):
                    value = value[:]
                elif type(value) == bpy_types.bpy_prop_array:
                    ## No to_list function
                    OutputDict["Props"][prop.identifier] = list(value)
                else:
                    if IsJsonSerializable(value):
                        OutputDict["Props"][prop.identifier] = value
                    else:
                        OutputDict["Props"][prop.identifier] = str(value)
            except Exception as e:
                print(e)
    OutputDict["textures"] = dict()
    if mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                OutputDict["textures"][node.name] = bpy.path.abspath(node.image.filepath)
    return OutputDict

def GetAllSceneMaterials():
    """
    Returns dict with additional info:
    { MeshName : { MatID: { 'material': Material, 'name': str, 'slot': MaterialSlot }}}
    """
    result = {}
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            if not HasParentOfName(obj, 'rigidbodies'):
                result[obj.name] = {}
                for mat_id, mat_slot in enumerate(obj.material_slots):
                    result[obj.name][mat_id] = MatToDict(mat_slot.material)
    return result

def SaveSceneMats(OutputJsonPath):
    with open(OutputJsonPath, 'w') as OutSceneMatJSON:
        # OutSceneMatJSON.write(str(GetAllSceneMaterials()))
        json.dump(GetAllSceneMaterials(), OutSceneMatJSON)

def CleanTargetObjects(TargetNameSet):
    """
    Deletes objects with any parent in TargetNameSet
    """
    RemovingObjects = list()
    for obj in bpy.data.objects:
        if HasParentOfNameInSet(obj, TargetNameSet):
            RemovingObjects.append(obj)

    for obj in RemovingObjects:
        bpy.data.objects.remove(obj, do_unlink=True)

def PortMMDToDAE(InputPath, OutputModelPath, OutputMatPath):
    # # Clear the current scene
    reset_blender()
    # Import MMD Model
    ImportMMDFile(InputPath)
    # Cleanup joints and rigidbodies
    CleanTargetObjects({'joints', 'rigidbodies'})
    # Export to Material
    SaveSceneMats(OutputMatPath)
    # Export to DAE
    ExportDAEFile(OutputModelPath)
    # # Clear the current scene
    reset_blender()

def EndsWithInSet(InputStr, PostFixSet):
    for CurrentPostFix in PostFixSet:
        if InputStr.endswith(CurrentPostFix):
            return True
    return False

def batch_convert(InputRoot, OutputRoot):
    # Supported extensions
    MMD_Model_ExtSet = {'.pmx', '.pmd'}

    TotalPortingCount = 0
    for CurrentRoot, Dirs, Files in os.walk(InputRoot):
        for CurrentFile in Files:
            if EndsWithInSet(CurrentFile, MMD_Model_ExtSet):
                CurrentFileInputPath = os.path.join(CurrentRoot, CurrentFile)
                CurrentFileOutputDir = os.path.join(OutputRoot, os.path.relpath(CurrentRoot, InputRoot))
                CurrentFilePrefix = os.path.splitext(CurrentFile)[0]
                ModelOutputPath = os.path.join(CurrentFileOutputDir, CurrentFilePrefix+"_Model.dae")
                MatOutputPath = os.path.join(CurrentFileOutputDir, CurrentFilePrefix+"_Mat.json")
                os.makedirs(CurrentFileOutputDir, exist_ok=True)
                PortMMDToDAE(CurrentFileInputPath, ModelOutputPath, MatOutputPath)
                TotalPortingCount += 1
    print(f"Finised: {TotalPortingCount} Files Processed.")

if __name__ == "__main__":
    input_Dir = r"D:\GAMES\Modding\Python_MaxScript_Workdir\GFA_Model_Weight_Transfer\MMD_Input_Sample"
    output_Dir = r"D:\GAMES\Modding\Python_MaxScript_Workdir\GFA_Model_Weight_Transfer\DAE_Output_Sample"
    # Ensure mmd_tools addon is enabled
    if not ensure_addon_enabled("mmd_tools"):
        print("Error: mmd_tools addon is not installed or cannot be enabled")
    else:
        batch_convert(input_Dir, output_Dir)
