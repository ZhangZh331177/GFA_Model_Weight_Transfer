import bpy
import os

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
    """Remove all objects from the current scene."""
    bpy.ops.wm.read_factory_settings(use_empty=True)

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
            ik_loop_factor=5,
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

def SaveSceneMats(OutputJsonPath)

def PortMMDToFBX(InputPath, OutputPath):
    """
    Import an MMD model (PMX/PMD) and export to FBX format.
    
    Args:
        InputPath (str): Path to the MMD model file (.pmx or .pmd)
        OutputPath (str): Path for the output FBX file (.fbx)
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    
    # Clear the current scene
    clear_scene()
    
    # Import MMD Model
    
    # Prepare model for FBX export
    prepare_for_export()
    
    # Export to FBX
    try:
        bpy.ops.export_scene.fbx(
            filepath=OutputPath,
            use_selection=False,
            global_scale=1.0,
            apply_scale_options='FBX_SCALE_ALL',
            use_mesh_modifiers=True,
            mesh_smooth_type='FACE',
            add_leaf_bones=False,
            primary_bone_axis='Y',
            secondary_bone_axis='X',
            use_armature_deform_only=True,
            bake_anim=False,
            path_mode='COPY',
            embed_textures=True
        )
        print(f"Successfully exported: {OutputPath}")
        return True
    except Exception as e:
        print(f"Error exporting to FBX: {e}")
        return False






def prepare_for_export():
    """Prepare the imported MMD model for FBX export."""
    
    # Find the MMD root object
    mmd_root = None
    for obj in bpy.context.scene.objects:
        if obj.mmd_type == 'ROOT':
            mmd_root = obj
            break
    
    if mmd_root:
        # Select the MMD root and make it active
        bpy.ops.object.select_all(action='DESELECT')
        mmd_root.select_set(True)
        bpy.context.view_layer.objects.active = mmd_root
        
        # Convert MMD model to Blender-friendly format (optional)
        try:
            bpy.ops.mmd_tools.convert_to_blender_compatible()
        except Exception:
            pass  # This operator may not exist in all versions
    
    # Select all objects for export
    bpy.ops.object.select_all(action='SELECT')
    
    # Apply transforms to all objects
    for obj in bpy.context.scene.objects:
        if obj.type in {'MESH', 'ARMATURE'}:
            bpy.context.view_layer.objects.active = obj
            try:
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            except Exception:
                pass


def batch_convert(input_folder, output_folder):
    """
    Batch convert all MMD models in a folder to FBX.
    
    Args:
        input_folder (str): Folder containing MMD models
        output_folder (str): Folder for output FBX files
    """
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Supported extensions
    extensions = ('.pmx', '.pmd')
    
    # Find and convert all MMD files
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(extensions):
            input_path = os.path.join(input_folder, filename)
            output_filename = os.path.splitext(filename)[0] + '.fbx'
            output_path = os.path.join(output_folder, output_filename)
            
            print(f"\nConverting: {filename}")
            PortMMDToFBX(input_path, output_path)
    
    print("\nBatch conversion complete!")


# =============================================================================
# Usage Examples
# =============================================================================

if __name__ == "__main__":
    # Ensure mmd_tools addon is enabled
    if not ensure_addon_enabled("mmd_tools"):
        print("Error: mmd_tools addon is not installed or cannot be enabled")
    else:
        reset_blender() # Addons will be disabled after resetting blender
        ensure_addon_enabled("mmd_tools")

    
        # Single file conversion
        input_file = r"C:\Models\character.pmx"
        output_file = r"C:\Models\character.fbx"
        
        PortMMDToFBX(input_file, output_file)
        
        # Batch conversion (uncomment to use)
        # batch_convert(r"C:\MMD_Models", r"C:\FBX_Output")
