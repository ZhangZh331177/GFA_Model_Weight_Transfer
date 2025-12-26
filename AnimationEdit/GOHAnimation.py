import os
from scipy.spatial.transform import Rotation, RotationSpline
from scipy.interpolate import make_interp_spline
import numpy as np
import struct
from SL_IK_Lib import GetRotatedVector, GetVectorRotationQuat
from SL_GOH_SKE_Lib import IsParentInGOHModificationSke, GetDirectChidsOfListInConstructionSke, GOHParentDictForConstruction
from multiprocessing import Pool

def LeftQuaternionXYZToRightHandQuaternionXYZW(X, Y, Z):
    W = np.sqrt(np.clip(1.0 - ((X**2) + (Y**2) + (Z**2)), 0.0, 1.0))
    return np.array([-X, -Y, Z, W], dtype=np.float32)

def RightHandQuaternionXYZWToLeftQuaternionXYZ(X, Y, Z, W):
    return np.array([-X, -Y, Z], dtype=np.float32)

def PositionFromLeftHandToRightHand(X, Y, Z):
    return np.array([X, Y, -Z], dtype=np.float32)

def PositionFromRightHandToLeftHand(X, Y, Z):
    return np.array([X, Y, -Z], dtype=np.float32)

def NormalizeQuaternion(InputArray):
    return InputArray / np.linalg.norm(InputArray, axis=-1, keepdims=True)

def AlignQuaternionForShortestPath(InputArray):
    OutputArray = InputArray.copy()
    for i in range(1, len(OutputArray)):
        if np.dot(OutputArray[i], OutputArray[i - 1]) < 0:
            OutputArray[i] = -OutputArray[i]
    return OutputArray

def AlignQuaternionForPositiveW(InputArray):
    OutputArray = InputArray.copy()
    OutputArray[OutputArray[:, 3] < 0] *= -1
    return OutputArray

class GOHAnim:
    B_POSITION = 0x01      # Bit 0: Position/translation data present
    B_ORIENTATION = 0x02   # Bit 1: Orientation/rotation data present  
    B_LEFT_HANDED = 0x04   # Bit 2: Left-handed coordinate system
    B_VISIBLE_ON = 0x08    # Bit 3: Bone is visible
    B_VISIBLE_OFF = 0x10   # Bit 4: Bone is hidden
    B_MESH = 0x20          # Bit 5: Mesh data present (not supported)

    def IsBoneExist(self, BoneName):
        BoneNameUpper = BoneName.upper()
        return BoneNameUpper in self.BoneNamesUpper

    def ExportFrameToCSV(self, frameID, outputPath):
        with open(outputPath, 'w') as OutFile:
            for NodeName, NodePos in zip(self.BoneNames, self.Pos[:,frameID,:]):
                OutFile.write(f"{NodeName}, {NodePos[0]}, {NodePos[1]}, {NodePos[2]}\n")

    def ApplyOverallPosOffset(self, InputOffsetArray, ExcludeBones = []):
        ExcludeBonesUpper = [BoneName.upper() for BoneName in ExcludeBones]
        UsingBoneIDList = [BoneID for BoneID, BoneNameUpper in enumerate(self.BoneNamesUpper) if BoneNameUpper not in ExcludeBonesUpper]
        self.Pos[UsingBoneIDList] += InputOffsetArray

    def GetSelfAndAllChildID(self, BoneName:str):
        BoneNameUpper = BoneName.upper()
        BoneIDList = [self.BoneNamesUpper.index(BoneNameUpper)]
        for CurrentBoneNameUpper in self.BoneNamesUpper:
            if IsParentInGOHModificationSke(CurrentBoneNameUpper, BoneNameUpper):
                BoneIDList.append(self.BoneNamesUpper.index(CurrentBoneNameUpper))
        return BoneIDList

    def GetNodePos(self, NodeName:str):
        NodeNameUpper = NodeName.upper()
        if NodeNameUpper not in self.BoneNamesUpper:
            raise ValueError(f"Target bone {NodeName} not found in current animation!")
        NodeID = self.BoneNamesUpper.index(NodeNameUpper)
        return self.Pos[NodeID].copy()

    def ApplyRotation(self, NodeName, frameID, RotationQuat):
        NodeNameUpper = NodeName.upper()
        if NodeNameUpper not in self.BoneNamesUpper:
            raise ValueError(f"Target bone {NodeName} not found in current animation!")
        SelfID = self.BoneNamesUpper.index(NodeNameUpper)
        AffectingNodeID = self.GetSelfAndAllChildID(NodeName)
        # Apply Rotation
        InputRotation = Rotation.from_quat(RotationQuat)
        AffectedNodeRotation = self.Rot[AffectingNodeID, frameID, :]
        NewRotation = (Rotation.from_quat(AffectedNodeRotation) * InputRotation)
        self.Rot[AffectingNodeID, frameID, :] = NewRotation.as_quat(canonical=True)
        # Apply Position
        AffectedNodePosition = self.Pos[AffectingNodeID, frameID, :]
        SelfNodePosition = self.Pos[SelfID, frameID, :]
        RelatedPosition = AffectedNodePosition - SelfNodePosition
        NewRelatedPosition = InputRotation.apply(RelatedPosition)
        self.Pos[AffectingNodeID, frameID, :] = SelfNodePosition + NewRelatedPosition

    def IKToPosition(self, ShoulderBoneName:str, ElbowBoneName:str, HandBoneName:str, ExpectedPositon, KeepRotationAfterHand = True):
        ShoulderBoneNameUpper = ShoulderBoneName.upper()
        ElbowBoneNameUpper = ElbowBoneName.upper()
        HandBoneNameUpper = HandBoneName.upper()
        
        if (ShoulderBoneNameUpper not in self.BoneNamesUpper):
            raise ValueError(f"Target bone {ShoulderBoneName} not found in current animation!")
        elif (ElbowBoneNameUpper not in self.BoneNamesUpper):
            raise ValueError(f"Target bone {ElbowBoneName} not found in current animation!")
        elif (HandBoneNameUpper not in self.BoneNamesUpper):
            raise ValueError(f"Target bone {HandBoneName} not found in current animation!")
        
        ShoulderNodeID = self.BoneNamesUpper.index(ShoulderBoneNameUpper)
        ElbowNodeID = self.BoneNamesUpper.index(ElbowBoneNameUpper)
        HandNodeID = self.BoneNamesUpper.index(HandBoneNameUpper)

        if KeepRotationAfterHand:
            HandOriginalRotation = Rotation.from_quat(self.Rot[HandNodeID].copy())

        # Perform IK
        for frameID in range(self.Pos.shape[1]):
            # Step1: Rotate Elbow
            ## Get Position
            ShoulderPos = self.Pos[ShoulderNodeID,frameID, :]
            ElbowPos = self.Pos[ElbowNodeID,frameID, :]
            HandPos = self.Pos[HandNodeID,frameID, :]
            ExpectedHandPos = ExpectedPositon[frameID]

            UpperArmVector = ElbowPos - ShoulderPos
            LowerArmVector = HandPos - ElbowPos
            ExpectedHandDistance = float(np.linalg.norm(ExpectedHandPos - ShoulderPos))
            RotatedLowerArmVector = GetRotatedVector(UpperArmVector, LowerArmVector, ExpectedHandDistance)
            ElbowAddingRotation = GetVectorRotationQuat(LowerArmVector, RotatedLowerArmVector)
            self.ApplyRotation(ElbowBoneNameUpper, frameID, ElbowAddingRotation)
            
            # Step2: Rotate Shoulder
            ## Refresh Position
            ShoulderPos = self.Pos[ShoulderNodeID,frameID, :]
            ElbowPos = self.Pos[ElbowNodeID,frameID, :]
            HandPos = self.Pos[HandNodeID,frameID, :]
            ExpectedHandPos = ExpectedPositon[frameID]

            FullArmVector = HandPos - ShoulderPos
            FullArmExpectedVector = ExpectedHandPos - ShoulderPos
            ShoulderAddingRotation = GetVectorRotationQuat(FullArmVector, FullArmExpectedVector)
            self.ApplyRotation(ShoulderBoneNameUpper, frameID, ShoulderAddingRotation)

        # Restore Hand Rotation
        if KeepRotationAfterHand:
            HandCurrentRotation = Rotation.from_quat(self.Rot[HandNodeID].copy())
            RelativeRotation = (HandOriginalRotation * HandCurrentRotation.inv()).as_quat(canonical=True)
            for frameID in range(self.Pos.shape[1]):
                self.ApplyRotation(HandBoneNameUpper, frameID, RelativeRotation[frameID])

    def Interpolate(self, method:str = "BSpline"):
        if method == "BSpline":
            for BoneID in range(self.Pos.shape[0]):
                # Interpolate Rotation
                currentRotCurve = self.Rot[BoneID]
                RotNanMask = np.max(np.isnan(currentRotCurve), axis=-1)
                if RotNanMask.any():
                    if RotNanMask.all():
                        raise ValueError(f"One of the bone with ID {BoneID} has no recorded Rotation key!")
                    InputRotFrames = np.where(np.logical_not(RotNanMask))[0]
                    InputRotValues = currentRotCurve[InputRotFrames]
                    InputRotValues = NormalizeQuaternion(InputRotValues)
                    InputRotValues = AlignQuaternionForShortestPath(InputRotValues)
                    RotSplineInterp = RotationSpline(InputRotFrames, Rotation.from_quat(InputRotValues))
                    RotSplineInterpResult = RotSplineInterp(np.arange(0, currentRotCurve.shape[0])).as_quat(canonical=True)
                    RotSplineInterpResult = AlignQuaternionForPositiveW(RotSplineInterpResult)
                    self.Rot[BoneID,:] = RotSplineInterpResult
                
                # Interpolate position
                currentPosCurve = self.Pos[BoneID]
                PosNanMask = np.max(np.isnan(currentPosCurve), axis=-1)
                if PosNanMask.any():
                    if PosNanMask.all():
                        raise ValueError(f"One of the bone with ID {BoneID} has no recorded key!")
                    InputPosFrames = np.where(np.logical_not(PosNanMask))[0]
                    InputPosValues = currentPosCurve[InputPosFrames]
                    SplineInterp = make_interp_spline(InputPosFrames, InputPosValues, k = min(3, len(InputPosFrames) - 1))
                    self.Pos[BoneID,:] = SplineInterp(np.arange(0, currentPosCurve.shape[0]))
        else:
            raise NotImplementedError(f"Required method {method} not implemented!")
    
    def ScaleBone(self, ParentNodeName, ChildNodeName, ScaleRatio):
        ParentNodeNameUpper = ParentNodeName.upper()
        ChildNodeNameUpper = ChildNodeName.upper()
        if not ParentNodeNameUpper in self.BoneNamesUpper:
            raise ValueError(f"Target bone {ParentNodeName} not found in current animation!")
        if not ChildNodeNameUpper in self.BoneNamesUpper:
            raise ValueError(f"Target bone {ChildNodeName} not found in current animation!")

        ParentNodeID = self.BoneNamesUpper.index(ParentNodeNameUpper)
        ChildNodeID = self.BoneNamesUpper.index(ChildNodeNameUpper)

        if np.isnan(self.Pos).any() == True:
            raise ValueError(f"Could not perform ScaleBone opreation in not interploated Animation!")
        
        ParentNodePos = self.Pos[ParentNodeID]
        ChildNodePos = self.Pos[ChildNodeID]
        OffsetValue = (ParentNodePos - ChildNodePos) * (1 - ScaleRatio)

        AffectingNodeID = self.GetSelfAndAllChildID(ChildNodeNameUpper)
        self.Pos[AffectingNodeID] += OffsetValue

    def ScaleBoneIfExist(self, ParentNodeName, ChildNodeName, ScaleRatio):
        ParentNodeNameUpper = ParentNodeName.upper()
        ChildNodeNameUpper = ChildNodeName.upper()
        if not ParentNodeNameUpper in self.BoneNamesUpper:
            return
        if not ChildNodeNameUpper in self.BoneNamesUpper:
            return
        self.ScaleBone(ParentNodeName, ChildNodeName, ScaleRatio)

    def ScaleNodeGroup(self, NodeNameList, ScaleRatio):
        NodeNameListUpper = [NodeName.upper() for NodeName in NodeNameList]
        for NodeNameUpper in NodeNameListUpper:
            if not NodeNameUpper in self.BoneNamesUpper:
                raise ValueError(f"Target bone {NodeNameUpper} not found in current animation!")
        
        NodeIDList = [self.BoneNamesUpper.index(NodeNameUpper) for NodeNameUpper in NodeNameListUpper]
        NodePosList = [self.Pos[NodeID] for NodeID in NodeIDList]
        NodeCenterPos = np.mean(np.array(NodePosList), axis=0)
        NodeOffsetList = [(NodeCenterPos - NodePos) * (1 - ScaleRatio) for NodePos in NodePosList]
        NodeAffectingNodeIDList = [self.GetSelfAndAllChildID(NodeNameUpper) for NodeNameUpper in NodeNameListUpper]
        for NodeOffset, NodeAffectingNodeID in zip(NodeOffsetList, NodeAffectingNodeIDList):
            self.Pos[NodeAffectingNodeID] += NodeOffset

    def __init__(self, InputFilePath):
        # === Read and check Header ===
        with open(InputFilePath, 'rb') as filePtr:
            # === FirstTag: EANM (FileHeadMarker) ===
            NextTag = filePtr.read(4)
            if NextTag != b'EANM':
                raise ValueError(f"Not a valid EANM file - missing EANM header, got {NextTag}")
            self.FileVer = struct.unpack('<I', filePtr.read(4))[0]
            # Check Version of file
            # supported_versions = {0x00030000, 0x00040000, 0x00050000, 0x00060000, 0x00060001}
            supported_versions = {0x00060000, 0x00060001} # Only FRM2 is implemented!
            if self.FileVer not in supported_versions:
                raise ValueError(f"Unsupported ANM version: 0x{self.FileVer:08X} for file {InputFilePath}")
            # === NextTAG: FRMS (FrameCount) ===
            NextTag = filePtr.read(4)
            if NextTag != b'FRMS':
                raise ValueError(f"Expected FRMS tag, got {NextTag}")
            self.FrameCount = struct.unpack('<I', filePtr.read(4))[0]
            # === NextTAG: BMAP (BoneMap) ===
            NextTag = filePtr.read(4)
            if NextTag != b'BMAP':
                raise ValueError(f"Expected BMAP tag, got {NextTag}")
            self.BoneCount = struct.unpack('<I', filePtr.read(4))[0]
            # Read bone names
            self.BoneNames = []
            self.BoneNamesUpper = []
            for _ in range(self.BoneCount):
                name_size = struct.unpack('<I', filePtr.read(4))[0]
                name = filePtr.read(name_size).decode('latin-1')
                self.BoneNames.append(name)
                self.BoneNamesUpper.append(name.upper())
            
            # === NextTAG: FRM2 (For New Versions like 00060001) ===
            self.Pos = np.full((self.BoneCount, self.FrameCount, 3), np.nan, dtype=np.float32)
            self.Rot = np.full((self.BoneCount, self.FrameCount, 4), np.nan, dtype=np.float32)
            self.Vis = np.full((self.BoneCount, self.FrameCount), -1, dtype=int)
            self.RawChunks = dict()
            while True:
                NextTag = filePtr.read(4)
                if not NextTag or len(NextTag) < 4:
                    break
                if NextTag != b'FRM2':
                    raise ValueError(f"Expected FRM2 tag for New format, Old format not Implemented yet!!!")
                else:
                    FrameID = struct.unpack('<H', filePtr.read(2))[0]
                    KeyFrameChunkCount = struct.unpack('<B', filePtr.read(1))[0]
                    self.RawChunks[FrameID] = dict()
                    
                    for _ in range(KeyFrameChunkCount):
                        BoneID = struct.unpack('<B', filePtr.read(1))[0]
                        ChunkFlags = struct.unpack('<H', filePtr.read(2))[0]
                        self.RawChunks[FrameID][BoneID] = ChunkFlags
                        
                        if ChunkFlags & GOHAnim.B_POSITION:
                            self.Pos[BoneID, FrameID, :] = PositionFromLeftHandToRightHand(*np.array(struct.unpack('<3f', filePtr.read(12)), dtype=np.float32))
                        
                        if ChunkFlags & GOHAnim.B_ORIENTATION:
                            # This is QuatXYZ not EULER XYZ!!!!!!
                            self.Rot[BoneID, FrameID, :] = LeftQuaternionXYZToRightHandQuaternionXYZW(*np.array(struct.unpack('<3f', filePtr.read(12)), dtype=np.float32))
                        
                        if ChunkFlags & GOHAnim.B_VISIBLE_ON:
                            self.Vis[BoneID, FrameID] = 1
                        elif ChunkFlags & GOHAnim.B_VISIBLE_OFF:
                            self.Vis[BoneID, FrameID] = 0

                        if ChunkFlags & GOHAnim.B_MESH:
                            raise ValueError("MESH data in animation is not supported")
                        
                        if ChunkFlags > 63:
                            raise ValueError(f"Unknown flags detected: 0x{ChunkFlags:04X}")
        self.Interpolate()
        # Cast Local Position and Rotation To Global position and Rotation
        RootBoneList = list()
        for NodeNameUpper in self.BoneNamesUpper:
            if NodeNameUpper not in GOHParentDictForConstruction.keys():
                RootBoneList.append(NodeNameUpper)
            elif GOHParentDictForConstruction[NodeNameUpper] not in self.BoneNamesUpper:
                RootBoneList.append(NodeNameUpper)

        CurrentBoneList = GetDirectChidsOfListInConstructionSke(self.BoneNamesUpper, RootBoneList)
        while CurrentBoneList:
            for CurrentBoneName in CurrentBoneList:
                CurrentBoneID = self.BoneNamesUpper.index(CurrentBoneName)
                ParentBoneName = GOHParentDictForConstruction[CurrentBoneName]
                ParentBoneID = self.BoneNamesUpper.index(ParentBoneName)
                for frameID in range(self.FrameCount):
                    ParentRotation = Rotation.from_quat(self.Rot[ParentBoneID, frameID][np.newaxis,:])
                    LocalRotation = Rotation.from_quat(self.Rot[CurrentBoneID, frameID][np.newaxis,:])
                    GlobalRotation = ParentRotation * LocalRotation
                    self.Rot[CurrentBoneID, frameID] = GlobalRotation.as_quat(canonical=True)
                    self.Pos[CurrentBoneID,frameID] = self.Pos[ParentBoneID,frameID] + ParentRotation.apply(self.Pos[CurrentBoneID,frameID])
            CurrentBoneList = GetDirectChidsOfListInConstructionSke(self.BoneNamesUpper, CurrentBoneList)
        
    def write(self, OutputFilePath):
        # Cast Global Position and Rotation To Local position and Rotation
        LocalPos = np.full((self.BoneCount, self.FrameCount, 3), np.nan, dtype=np.float32)
        LocalRot = np.full((self.BoneCount, self.FrameCount, 4), np.nan, dtype=np.float32)
        for BoneID, BoneNameUpper in enumerate(self.BoneNamesUpper):
            # Write Values for Root Bones
            if BoneNameUpper not in GOHParentDictForConstruction.keys():
                LocalPos[BoneID] = self.Pos[BoneID]
                LocalRot[BoneID] = self.Rot[BoneID]
                negative_w = LocalRot[BoneID, :, 3] < 0
                LocalRot[BoneID, negative_w] = -LocalRot[BoneID, negative_w]
                continue
            elif GOHParentDictForConstruction[BoneNameUpper] not in self.BoneNamesUpper:
                LocalPos[BoneID] = self.Pos[BoneID]
                LocalRot[BoneID] = self.Rot[BoneID]
                negative_w = LocalRot[BoneID, :, 3] < 0
                LocalRot[BoneID, negative_w] = -LocalRot[BoneID, negative_w]
                continue
            else:
                ParentBoneID = self.BoneNamesUpper.index(GOHParentDictForConstruction[BoneNameUpper])
                ParentRotation = Rotation.from_quat(self.Rot[ParentBoneID])
                GlobalRotation = Rotation.from_quat(self.Rot[BoneID])
                LocalRotation = ParentRotation.inv() * GlobalRotation
                LocalRot[BoneID] = LocalRotation.as_quat(canonical=True)
                negative_w = LocalRot[BoneID, :, 3] < 0
                LocalRot[BoneID, negative_w] = -LocalRot[BoneID, negative_w]
                RelatedTransform = self.Pos[BoneID] - self.Pos[ParentBoneID]
                UnRotatedTransform = ParentRotation.inv().apply(RelatedTransform)
                LocalPos[BoneID] = UnRotatedTransform
        with open(OutputFilePath, 'wb') as filePtr:
            # === Write Header: EANM ===
            filePtr.write(b'EANM')
            filePtr.write(struct.pack('<I', 0x00060001))  # Version 0x00060001
            
            # === Write FRMS (FrameCount) ===
            filePtr.write(b'FRMS')
            filePtr.write(struct.pack('<I', self.FrameCount))
            
            # === Write BMAP (BoneMap) ===
            filePtr.write(b'BMAP')
            filePtr.write(struct.pack('<I', self.BoneCount))
            
            # Write bone names
            for name in self.BoneNames:
                name_bytes = name.encode('latin-1')
                filePtr.write(struct.pack('<I', len(name_bytes)))
                filePtr.write(name_bytes)
            
            # === Write FRM2 sections ===
            for frame_id, frame_chunks in self.RawChunks.items():
                filePtr.write(b'FRM2')
                filePtr.write(struct.pack('<H', frame_id))          # FrameID: uint16
                filePtr.write(struct.pack('<B', len(frame_chunks)))  # KeyFrameChunkCount: uint8
                for BoneID, ChunkFlags in frame_chunks.items():
                    filePtr.write(struct.pack('<B', BoneID))       # BoneID: uint8
                    filePtr.write(struct.pack('<H', ChunkFlags))   # ChunkFlags: uint16
                    if ChunkFlags & GOHAnim.B_POSITION:
                        LeftHandedPos = PositionFromRightHandToLeftHand(*LocalPos[BoneID, frame_id, :])
                        filePtr.write(struct.pack('<3f', *LeftHandedPos))
                    if ChunkFlags & GOHAnim.B_ORIENTATION:
                        LeftHandedRot = RightHandQuaternionXYZWToLeftQuaternionXYZ(*LocalRot[BoneID, frame_id, :])
                        filePtr.write(struct.pack('<3f', *LeftHandedRot))

            # for frame_id in range(self.FrameCount):
            #     # Collect bones with keyframe data in this frame
            #     keyframe_chunks = []
                
            #     for bone_id in range(self.BoneCount):
            #         chunk_flags = 0
            #         has_pos = False
            #         has_rot = False
                    
            #         # Check position (NaN means no keyframe)
            #         if not np.isnan(LocalPos[bone_id, frame_id, 0]):
            #             chunk_flags |= GOHAnim.B_POSITION
            #             has_pos = True
                    
            #         # Check rotation (NaN means no keyframe)
            #         if not np.isnan(LocalRot[bone_id, frame_id, 0]):
            #             chunk_flags |= GOHAnim.B_ORIENTATION
            #             has_rot = True
                    
            #         # Check visibility (-1 means no keyframe)
            #         vis_value = self.Vis[bone_id, frame_id]
            #         if vis_value == 1:
            #             chunk_flags |= GOHAnim.B_VISIBLE_ON
            #         elif vis_value == 0:
            #             chunk_flags |= GOHAnim.B_VISIBLE_OFF
                    
            #         # Only add chunk if there's any data
            #         if chunk_flags != 0:
            #             chunk_flags |= GOHAnim.B_LEFT_HANDED
            #             keyframe_chunks.append((bone_id, chunk_flags, has_pos, has_rot))
                
            #     # Only write FRM2 block if there are keyframe chunks for this frame
            #     if keyframe_chunks:
            #         filePtr.write(b'FRM2')
            #         filePtr.write(struct.pack('<H', frame_id))          # FrameID: uint16
            #         filePtr.write(struct.pack('<B', len(keyframe_chunks)))  # KeyFrameChunkCount: uint8
                    
            #         for bone_id, chunk_flags, has_pos, has_rot in keyframe_chunks:
            #             filePtr.write(struct.pack('<B', bone_id))       # BoneID: uint8
            #             filePtr.write(struct.pack('<H', chunk_flags))   # ChunkFlags: uint16
                        
            #             if has_pos:
            #                 LeftHandedPos = PositionFromRightHandToLeftHand(*LocalPos[bone_id, frame_id, :])
            #                 filePtr.write(struct.pack('<3f', *LeftHandedPos))
                        
            #             if has_rot:
            #                 LeftHandedRot = RightHandQuaternionXYZWToLeftQuaternionXYZ(*LocalRot[bone_id, frame_id, :])
            #                 filePtr.write(struct.pack('<3f', *LeftHandedRot))

def ProcessAnimFile(inputPath, outputPath):
    if os.path.exists(outputPath):
        return
    os.makedirs(os.path.dirname(outputPath), exist_ok=True)
    InputAnimation = GOHAnim(inputPath)
    # Record Positions For later IK
    if InputAnimation.IsBoneExist("foot3L") and InputAnimation.IsBoneExist("foot3R"):
        StartLFootPosition = InputAnimation.GetNodePos("foot3L")
        StartRFootPosition = InputAnimation.GetNodePos("foot3R")
    if InputAnimation.IsBoneExist("Hand3L"):
        StartLHandPosition = InputAnimation.GetNodePos("Hand3L")
    if InputAnimation.IsBoneExist("Hand3R"):
        StartRHandPosition = InputAnimation.GetNodePos("Hand3R")
    # LowerLegLength * 1.16
    InputAnimation.ScaleBoneIfExist('foot2L', "Bone06", 1.16)
    InputAnimation.ScaleBoneIfExist('foot2L', "foot3L", 1.16)
    InputAnimation.ScaleBoneIfExist('foot2R', "Bone03", 1.16)
    InputAnimation.ScaleBoneIfExist('foot2R', "foot3R", 1.16)
    # UpperLegLength * 0.99
    InputAnimation.ScaleBoneIfExist('foot1L', "foot2L", 0.99)
    InputAnimation.ScaleBoneIfExist('foot1R', "foot2R", 0.99)
    # PelvisWidth * 0.83
    if InputAnimation.IsBoneExist("foot1R") and InputAnimation.IsBoneExist("foot1L"):
        InputAnimation.ScaleNodeGroup(['foot1R', "foot1L"], 0.83)
    # LowerBody * 1.09
    InputAnimation.ScaleBoneIfExist('Body', "IK_LeftRight", 1.09)
    # Clavicle * 0.78
    InputAnimation.ScaleBoneIfExist('IK_UpDown', "Clavicle_left", 0.78)
    InputAnimation.ScaleBoneIfExist('IK_UpDown', "Clavicle_right", 0.78)
    # Neck * 0.75
    InputAnimation.ScaleBoneIfExist('IK_UpDown', "Head", 0.78)
    # ClavicleWidth * 0.43
    if InputAnimation.IsBoneExist("Clavicle_left") and InputAnimation.IsBoneExist("Clavicle_right"):
        InputAnimation.ScaleNodeGroup(['Clavicle_left', "Clavicle_right"], 0.43)
    # Hand1L * 1.05 / Hand1R * 0.91
    InputAnimation.ScaleBoneIfExist('Clavicle_left', "Hand1L", 1.05)
    InputAnimation.ScaleBoneIfExist('Clavicle_right', "Hand1R", 0.91)
    # Hand2_LR * 0.80
    InputAnimation.ScaleBoneIfExist('Hand1L', "Hand2L", 0.80)
    InputAnimation.ScaleBoneIfExist('Hand1R', "Hand2R", 0.80)
    # Hand3_LR * 0.90
    InputAnimation.ScaleBoneIfExist('Hand2L', "Hand_rot1L", 0.90)
    InputAnimation.ScaleBoneIfExist('Hand2L', "Hand3L", 0.90)
    InputAnimation.ScaleBoneIfExist('Hand2L', "left_hand", 0.90)
    InputAnimation.ScaleBoneIfExist('Hand2R', "Hand_rot1R", 0.90)
    InputAnimation.ScaleBoneIfExist('Hand2R', "Hand3R", 0.90)
    InputAnimation.ScaleBoneIfExist('Hand2R', "right_hand", 0.90)

    # IK
    ## Initial
    if InputAnimation.IsBoneExist("foot3L") and InputAnimation.IsBoneExist("foot3R"):
        CurrentLFootPosition = InputAnimation.GetNodePos("foot3L")
        CurrentRFootPosition = InputAnimation.GetNodePos("foot3R")
        OverallPosOffset = ((StartLFootPosition + StartRFootPosition) - (CurrentLFootPosition + CurrentRFootPosition)) / 2
        InputAnimation.ApplyOverallPosOffset(OverallPosOffset, ExcludeBones=["BASIS"])
    ## Full
    if InputAnimation.IsBoneExist("foot3L") and InputAnimation.IsBoneExist("foot3R"):
        InputAnimation.IKToPosition('foot1L','foot2L','foot3L', StartLFootPosition)
        InputAnimation.IKToPosition('foot1R','foot2R','foot3R', StartRFootPosition)
    if InputAnimation.IsBoneExist("Hand3L"):
        InputAnimation.IKToPosition('Hand1L','Hand2L','Hand3L', StartLHandPosition)
    if InputAnimation.IsBoneExist("Hand3R"):
        InputAnimation.IKToPosition('Hand1R','Hand2R','Hand3R', StartRHandPosition)
    InputAnimation.ExportFrameToCSV(0, "After.csv")
    # ## Write
    InputAnimation.write(outputPath)

def TryProcessAnimFile(*Params):
    try:
        ProcessAnimFile(*Params)
    except Exception as e:
        print(f"Warning: {e}!")


if __name__== "__main__":
    # # # DEBUG
    # InputAnim = GOHAnim(r"C:\Users\simon\Downloads\AnimationEdit\anim_idle_02.anm")
    # InputAnim.ExportFrameToCSV(1, r"C:\Users\simon\Downloads\AnimationEdit\Before.csv")
    # InputAnim.write(r"C:\Users\simon\Downloads\AnimationEdit\anim_idle_02_Refit.anm")
    # GOHAnim(r"C:\Users\simon\Downloads\AnimationEdit\anim_idle_02_Refit.anm").ExportFrameToCSV(1, r"C:\Users\simon\Downloads\AnimationEdit\After.csv")

    # # Run
    WorkerPool = Pool(32)
    InputRoot = r"C:\Users\simon\Downloads\AnimationEdit\animation"
    OutputRoot = r"C:\Users\simon\Downloads\AnimationEdit\animation_patch\animation"
    TaskList = list()
    for root, dirs, files in os.walk(InputRoot):
        for file in files:
            if file.endswith(".anm"):
                inputPath = os.path.join(root, file)
                outputPath = os.path.join(OutputRoot, os.path.relpath(inputPath, InputRoot))
                TaskList.append([inputPath, outputPath])
    # [ProcessAnimFile(*Task) for Task in TaskList]
    WorkerPool.starmap(TryProcessAnimFile, TaskList)