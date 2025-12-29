import numpy as np
from scipy.spatial.transform import Rotation
# TargetBoneVector != Find_YZ_Rotation(CurrentRotation, CurrentBoneVector, TargetBoneVector).apply(CurrentRotation.inv(CurrentBoneVector))
def angular_diff(a, b):
    return np.abs(np.arctan2(np.sin(a - b), np.cos(a - b)))

def Find_YZ_Rotation(CurrentRotation:Rotation, CurrentBoneVector:np.ndarray, TargetBoneVector:np.ndarray):
    """
    Find new Euler XYZ rotation (only changing Y and Z) to align bone to target.
    
    Parameters:
    - current_rotation_euler: Current Euler angles [x, y, z] in radians (XYZ order)
    - current_bone_vector: Current bone direction vector (3D)
    - target_bone_vector: Target bone direction vector (3D)
    
    Returns:
    - new_euler: New Rotation
    """
    # Normalize input vectors
    CurrentBoneUnitVector = CurrentBoneVector.copy() / np.linalg.norm(CurrentBoneVector, axis=-1, keepdims=True)
    TargetBoneUnitVector = TargetBoneVector.copy() / np.linalg.norm(TargetBoneVector, axis=-1, keepdims=True)
    
    # Get rest pose bone vector (before any rotation)
    CurrentBoneUnitRestedVector = CurrentRotation.inv().apply(CurrentBoneUnitVector)
    
    # X angle stays fixed
    CurrentRotationEuler = CurrentRotation.as_euler(seq="xyz")
    New_X_Rot = CurrentRotationEuler[:,0]
    
    # Apply only X rotation to get intermediate vector
    CurrentBoneUnitXRotatedVector = Rotation.from_euler('X', New_X_Rot).apply(CurrentBoneUnitRestedVector)

    CurrentBoneUnitXRotatedVector_X, CurrentBoneUnitXRotatedVector_Y, CurrentBoneUnitXRotatedVector_Z = CurrentBoneUnitXRotatedVector.T
    TargetBoneUnitVectorX, TargetBoneUnitVectorY, TargetBoneUnitVectorZ = TargetBoneUnitVector.T
    
    # Solve for Y angle (XZ plane): tz = -vx*sin(y) + vz*cos(y)
    CurrentBoneUnitXRotatedVector_XZ_ProjectionLength = np.sqrt(CurrentBoneUnitXRotatedVector_X**2 + CurrentBoneUnitXRotatedVector_Z**2)
    
    New_Y_Rot = np.zeros_like(New_X_Rot)
    
    XZ_LengthMask = CurrentBoneUnitXRotatedVector_XZ_ProjectionLength >= 1e-10
    New_Y_Rot[np.logical_not(XZ_LengthMask)] = CurrentRotationEuler[:,1][np.logical_not(XZ_LengthMask)]

    XZ_CosineValue = np.clip(TargetBoneUnitVectorZ[XZ_LengthMask] / CurrentBoneUnitXRotatedVector_XZ_ProjectionLength[XZ_LengthMask], -1.0, 1.0)
    XZ_AlphaValue = np.arctan2(CurrentBoneUnitXRotatedVector_X[XZ_LengthMask], CurrentBoneUnitXRotatedVector_Z[XZ_LengthMask])

    Current_Y_Rot = CurrentRotationEuler[:,1][XZ_LengthMask]
    New_Y_Rot_Var_1 = np.arccos(XZ_CosineValue) - XZ_AlphaValue
    New_Y_Rot_Var_2 = -np.arccos(XZ_CosineValue) - XZ_AlphaValue

    New_Y_Rot_Var_1_Diff = angular_diff(New_Y_Rot_Var_1, Current_Y_Rot)
    New_Y_Rot_Var_2_Diff = angular_diff(New_Y_Rot_Var_2, Current_Y_Rot)
    New_Y_Rot_Var_2_Mask = New_Y_Rot_Var_1_Diff > New_Y_Rot_Var_2_Diff
    New_Y_Rot_Var_1[New_Y_Rot_Var_2_Mask] = New_Y_Rot_Var_2[New_Y_Rot_Var_2_Mask]

    New_Y_Rot[XZ_LengthMask] = New_Y_Rot_Var_1
    
    # Apply Y rotation to get intermediate vector
    CurrentBoneUnitXYRotatedVector = Rotation.from_euler('Y', New_Y_Rot).apply(CurrentBoneUnitXRotatedVector)
    CurrentBoneUnitXYRotatedVector_X, CurrentBoneUnitXYRotatedVector_Y, CurrentBoneUnitXYRotatedVector_Z = CurrentBoneUnitXYRotatedVector.T
    
    # Solve for Z angle (XY plane)
    New_Z_Rot = np.zeros_like(New_X_Rot)
    XY_LengthMask = np.logical_or(abs(CurrentBoneUnitXYRotatedVector_X) > 1e-10, abs(CurrentBoneUnitXYRotatedVector_Y) > 1e-10)
    New_Z_Rot[np.logical_not(XY_LengthMask)] = CurrentRotationEuler[:,2][np.logical_not(XY_LengthMask)]
    New_Z_Rot[XY_LengthMask] = np.arctan2(
        (TargetBoneUnitVectorY[XY_LengthMask] * CurrentBoneUnitXYRotatedVector_X[XY_LengthMask]) - 
        (TargetBoneUnitVectorX[XY_LengthMask] * CurrentBoneUnitXYRotatedVector_Y[XY_LengthMask]), 
        (TargetBoneUnitVectorX[XY_LengthMask] * CurrentBoneUnitXYRotatedVector_X[XY_LengthMask]) + 
        (TargetBoneUnitVectorY[XY_LengthMask] * CurrentBoneUnitXYRotatedVector_Y[XY_LengthMask]))
    
    return Rotation.from_euler("xyz", np.stack([New_X_Rot, New_Y_Rot, New_Z_Rot], axis=-1))