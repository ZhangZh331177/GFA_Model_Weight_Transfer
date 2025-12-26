import numpy as np

def GetRotatedVector(VectorA:np.ndarray, VectorB:np.ndarray, ExpectedLength:float):
    Length_VecA = np.linalg.norm(VectorA)
    Length_VecB = np.linalg.norm(VectorB)
    
    # Validate inputs
    if Length_VecA < 1e-10:
        raise ValueError("Vector A has zero length")
    elif Length_VecB < 1e-10:
        raise ValueError("Vector B has zero length")
    elif ExpectedLength < 0:
        raise ValueError("ExpectedLength must be non-negative")
    elif np.linalg.norm(np.cross(VectorA, VectorB)) / (Length_VecA * Length_VecB) < 1e-10:
        raise ValueError("Vector A and Vector B are parallel")
    
    # Get UnitVector for VectorA
    Unit_VecA = VectorA / Length_VecA

    # Edge cases
    if ExpectedLength >= Length_VecA + Length_VecB:
        return Length_VecB * Unit_VecA
    elif ExpectedLength <= abs(Length_VecA - Length_VecB):
        return -(Length_VecB * Unit_VecA)
    
    # Normal case: solve for C in the plane of A and B
    # C = alpha * Unit_VecA + beta * B_perp_hat
    
    # Get unit vector perpendicular to A, in the plane of A and B
    B_perp = VectorB - np.dot(VectorB, Unit_VecA) * Unit_VecA
    B_perp_hat = B_perp / np.linalg.norm(B_perp)
    
    # Solve constraints:
    # |A + C|² = L²  →  alpha = (L² - a² - b²) / (2a)
    # |C|² = b²      →  beta = √(b² - alpha²)
    alpha = (ExpectedLength**2 - Length_VecA**2 - Length_VecB**2) / (2 * Length_VecA)
    beta = np.sqrt(max(0, Length_VecB**2 - alpha**2))
    
    return alpha * Unit_VecA + beta * B_perp_hat

from scipy.spatial.transform import Rotation

def GetVectorRotationQuat(VectorA:np.ndarray, VectorB:np.ndarray):
    """
    Compute the quaternion that rotates vec_a to vec_b.
    
    Parameters:
        vec_a: 3D vector (source)
        vec_b: 3D vector (target)
    
    Returns:
        Quaternion as [x, y, z, w] (scipy convention)
    """
    # Normalize vectors
    Unit_VecA = VectorA / np.linalg.norm(VectorA)
    Unit_VecB = VectorB / np.linalg.norm(VectorB)
    
    # Rotation axis (cross product)
    RotationAxis = np.cross(Unit_VecA, Unit_VecB)
    RotationAxisNorm = np.linalg.norm(RotationAxis)
    RotationAxis = RotationAxis / RotationAxisNorm
    
    # Dot product for angle
    Unit_Vec_Dot = np.clip(np.dot(Unit_VecA, Unit_VecB), -1.0, 1.0)
    
    # Edge cases (parallel vectors)
    if RotationAxisNorm < 1e-10:
        if Unit_Vec_Dot > 0:
            # Same direction → identity quaternion
            return np.array([0.0, 0.0, 0.0, 1.0])
        else:
            # Opposite direction → 180° rotation around any perpendicular axis
            perp = np.array([1, 0, 0]) if abs(Unit_VecA[0]) < 0.9 else np.array([0, 1, 0])
            RotationAxis = np.cross(Unit_VecA, perp)
            RotationAxis = RotationAxis / np.linalg.norm(RotationAxis)
            return np.array([RotationAxis[0], RotationAxis[1], RotationAxis[2], 0.0])
        
    return Rotation.from_rotvec(RotationAxis * np.arccos(Unit_Vec_Dot)).as_quat(canonical = False)