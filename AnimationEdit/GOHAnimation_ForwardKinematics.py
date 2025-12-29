import os
from scipy.spatial.transform import Rotation, RotationSpline
from scipy.interpolate import make_interp_spline
import numpy as np
import struct
from SL_IK_Lib import Find_YZ_Rotation
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
    
    def GetLocalRot(self, BoneName):
        BoneNameUpper = BoneName.upper()
        
        if (BoneNameUpper not in self.BoneNamesUpper):
            raise ValueError(f"Target bone {BoneName} not found in current animation!")
        BoneID = self.BoneNamesUpper.index(BoneNameUpper)
        GlobalRotation = Rotation.from_quat(self.Rot[BoneID])

        if GOHParentDictForConstruction[BoneName.upper()] not in self.BoneNamesUpper:
            # Root Bone
            return GlobalRotation
        else:
            ParentBoneID = self.BoneNamesUpper.index(GOHParentDictForConstruction[BoneNameUpper])
            ParentRotation = Rotation.from_quat(self.Rot[ParentBoneID])
            LocalRotation = ParentRotation.inv() * GlobalRotation
            return LocalRotation

    def GetLocalPos(self, BoneName):
        BoneNameUpper = BoneName.upper()
        
        if (BoneNameUpper not in self.BoneNamesUpper):
            raise ValueError(f"Target bone {BoneName} not found in current animation!")
        BoneID = self.BoneNamesUpper.index(BoneNameUpper)
        ParentBoneID = self.BoneNamesUpper.index(GOHParentDictForConstruction[BoneNameUpper])

        ParentRotation = Rotation.from_quat(self.Rot[ParentBoneID])
        RelatedPos = self.Pos[BoneID] - self.Pos[ParentBoneID]
        UnRotatedRelatedPos = ParentRotation.inv().apply(RelatedPos)
        return UnRotatedRelatedPos

    def GetLocalPosByID(self, BoneID):
        return self.GetLocalPos(self.BoneNamesUpper[BoneID])
    
    def ApplyLocalPos(self, BoneName, NewLocalPos):
        BoneNameUpper = BoneName.upper()
        
        if (BoneNameUpper not in self.BoneNamesUpper):
            raise ValueError(f"Target bone {BoneName} not found in current animation!")
        BoneID = self.BoneNamesUpper.index(BoneNameUpper)

        if GOHParentDictForConstruction[BoneName.upper()] not in self.BoneNamesUpper:
            # Root Bone
            PosOffset = NewLocalPos - self.Pos[BoneID]
            AffectingNodeID = self.GetSelfAndAllChildID(BoneNameUpper)
            self.Pos[AffectingNodeID] += PosOffset
        else:
            ## Local Pos by parent
            ParentBoneID = self.BoneNamesUpper.index(GOHParentDictForConstruction[BoneNameUpper])

            ParentRotation = Rotation.from_quat(self.Rot[ParentBoneID])
            RelatedPos = ParentRotation.apply(NewLocalPos)
            PosOffset = (self.Pos[ParentBoneID] + RelatedPos) - self.Pos[BoneID]
            
            AffectingNodeID = self.GetSelfAndAllChildID(BoneNameUpper)
            self.Pos[AffectingNodeID] += PosOffset

    def ApplyLocalPosByID(self, BoneID, NewLocalPos):
        return self.ApplyLocalPos(self.BoneNamesUpper[BoneID], NewLocalPos)
    
    def ApplyLocalPosIfExist(self, BoneName, NewLocalPos):
        if BoneName.upper() not in self.BoneNamesUpper:
            return
        self.ApplyLocalPos(BoneName, NewLocalPos)

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

    def GetSelfAndAllChildIDNOExistanceAssumption(self, BoneName:str):
        BoneNameUpper = BoneName.upper()
        BoneIDList = []
        if BoneNameUpper in self.BoneNamesUpper:
            BoneIDList.append(self.BoneNamesUpper.index(BoneNameUpper))
        for CurrentBoneNameUpper in self.BoneNamesUpper:
            if IsParentInGOHModificationSke(CurrentBoneNameUpper, BoneNameUpper):
                BoneIDList.append(self.BoneNamesUpper.index(CurrentBoneNameUpper))
        return BoneIDList
    
    def GetNodePosByID(self, NodeID:int):
        return self.Pos[NodeID].copy()
    
    def GetNodePosByName(self, NodeName:str):
        NodeNameUpper = NodeName.upper()
        if NodeNameUpper not in self.BoneNamesUpper:
            raise ValueError(f"Target bone {NodeName} not found in current animation!")
        NodeID = self.BoneNamesUpper.index(NodeNameUpper)
        return self.Pos[NodeID].copy()

    def SetElbowRotation(self, NodeName, AngelArr, ElbowPositive):
        NodeNameUpper = NodeName.upper()
        if NodeNameUpper not in self.BoneNamesUpper:
            raise ValueError(f"Target bone {NodeName} not found in current animation!")
        SelfID = self.BoneNamesUpper.index(NodeNameUpper)
        # Get Rotation
        if ElbowPositive:
            EulerRotation = np.array([(0,0, 180 - Angel) for Angel in AngelArr]) # Fully extended to 180 degrees = 0
        else:
            EulerRotation = np.array([(0,0, -(180 - Angel)) for Angel in AngelArr]) # Fully extended to 180 degrees = 0, neg values
        NewLocalRotation = Rotation.from_euler("XYZ", EulerRotation, degrees=True)
        if GOHParentDictForConstruction[NodeNameUpper] not in self.BoneNamesUpper:
            NewGlobalRotation = NewLocalRotation
        else:
            ParentID = self.BoneNamesUpper.index(GOHParentDictForConstruction[NodeNameUpper])
            ParentRotation = Rotation.from_quat(self.Rot[ParentID, :])
            NewGlobalRotation = ParentRotation * NewLocalRotation
        
        CurrentGlobalRotation = Rotation.from_quat(self.Rot[SelfID, :])
        ApplyingRotation = NewGlobalRotation * CurrentGlobalRotation.inv()

        # Apply
        AffectingNodeIDList = self.GetSelfAndAllChildID(NodeName)
        # Apply rotation to childs
        for AffectingNodeID in AffectingNodeIDList:
            NodeGlobalRotation = Rotation.from_quat(self.Rot[AffectingNodeID, :])
            NodeNewGlobalRotation = ApplyingRotation * NodeGlobalRotation
            self.Rot[AffectingNodeID, :] = NodeNewGlobalRotation.as_quat(canonical=True)
            
            NodeLocalTransform = self.Pos[AffectingNodeID, :] - self.Pos[SelfID, :]
            NodeNewLocalTransform = ApplyingRotation.apply(NodeLocalTransform)
            self.Pos[AffectingNodeID, :] = self.Pos[SelfID, :] + NodeNewLocalTransform

    def IKToPosition(self, ShoulderBoneName:str, ElbowBoneName:str, HandBoneName:str, ExpectedPositon, ElbowPositive, HandBoneApplyNameList = None, KeepRotationAfterHand = True):
        ShoulderBoneNameUpper = ShoulderBoneName.upper()
        ElbowBoneNameUpper = ElbowBoneName.upper()
        HandBoneNameUpper = HandBoneName.upper()
        if HandBoneApplyNameList == None:
            HandBoneApplyNameList = [HandBoneName, ]
        
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
        ShoulderPos = self.Pos[ShoulderNodeID, :]
        ElbowPos = self.Pos[ElbowNodeID, :]
        HandPos = self.Pos[HandNodeID, :]

        # Elbow IK
        UpperArmLength = np.linalg.norm(ShoulderPos - ElbowPos, axis=-1)
        LowerArmLength = np.linalg.norm(ElbowPos - HandPos, axis=-1)
        TargetLength = np.linalg.norm(ShoulderPos - ExpectedPositon, axis=-1)

        # Law of cosines: cos(C) = (a² + b² - c²) / (2ab)
        AngelConsine = np.clip((UpperArmLength**2 + LowerArmLength**2 - TargetLength**2) / (2 * UpperArmLength * LowerArmLength), -1, 1)
        IK_Elbow_Angel = np.degrees(np.arccos(AngelConsine))
        IK_Elbow_Angel[np.where(TargetLength > (UpperArmLength + LowerArmLength))] = 180.0
        self.SetElbowRotation(ElbowBoneName, IK_Elbow_Angel, ElbowPositive)

        # Shoulder IK
        ShoulderLocalRotation = self.GetLocalRot(ShoulderBoneNameUpper)
        FullArmGlobalVector = self.Pos[HandNodeID, :] - self.Pos[ShoulderNodeID, :]
        FullArmTargetGlobalVector = ExpectedPositon - self.Pos[ShoulderNodeID, :]
        if GOHParentDictForConstruction[ShoulderBoneNameUpper] not in self.BoneNamesUpper:
            # Shoulder is Root Bone
            ShoulderNewGlobalRotation = Find_YZ_Rotation(ShoulderLocalRotation, FullArmGlobalVector, FullArmTargetGlobalVector)
        else:
            ParentID = self.BoneNamesUpper.index(GOHParentDictForConstruction[ShoulderBoneNameUpper])
            ParentRotation = Rotation.from_quat(self.Rot[ParentID])
            FullArmLocalVector = ParentRotation.inv().apply(FullArmGlobalVector)
            FullArmTargetLocalVector = ParentRotation.inv().apply(FullArmTargetGlobalVector)
            ShoulderNewLocalRotation = Find_YZ_Rotation(ShoulderLocalRotation, FullArmLocalVector, FullArmTargetLocalVector)
            ShoulderNewGlobalRotation = ParentRotation * ShoulderNewLocalRotation

        ApplyingRotation = ShoulderNewGlobalRotation * Rotation.from_quat(self.Rot[ShoulderNodeID]).inv()

        # Apply
        AffectingNodeIDList = self.GetSelfAndAllChildID(ShoulderBoneName)

        # Apply rotation to childs
        for AffectingNodeID in AffectingNodeIDList:
            NodeGlobalRotation = Rotation.from_quat(self.Rot[AffectingNodeID, :])
            NodeNewGlobalRotation = ApplyingRotation * NodeGlobalRotation
            self.Rot[AffectingNodeID, :] = NodeNewGlobalRotation.as_quat(canonical=True)
            
            NodeLocalTransform = self.Pos[AffectingNodeID, :] - self.Pos[ShoulderNodeID, :]
            NodeNewLocalTransform = ApplyingRotation.apply(NodeLocalTransform)
            self.Pos[AffectingNodeID, :] = self.Pos[ShoulderNodeID, :] + NodeNewLocalTransform

        # Restore Hand Rotation
        if KeepRotationAfterHand:
            HandCurrentRotation = Rotation.from_quat(self.Rot[HandNodeID].copy())
            ApplyingRotation = HandOriginalRotation * HandCurrentRotation.inv()
            
            # Apply
            AffectingNodeIDSet = set()
            for ApplyName in HandBoneApplyNameList:
                AffectingNodeIDSet.update(self.GetSelfAndAllChildIDNOExistanceAssumption(ApplyName))
            AffectingNodeIDList = list(AffectingNodeIDSet)

            # Apply rotation to childs
            for AffectingNodeID in AffectingNodeIDList:
                NodeGlobalRotation = Rotation.from_quat(self.Rot[AffectingNodeID, :])
                NodeNewGlobalRotation = ApplyingRotation * NodeGlobalRotation
                self.Rot[AffectingNodeID, :] = NodeNewGlobalRotation.as_quat(canonical=True)
                
                NodeLocalTransform = self.Pos[AffectingNodeID, :] - self.Pos[HandNodeID, :]
                NodeNewLocalTransform = ApplyingRotation.apply(NodeLocalTransform)
                self.Pos[AffectingNodeID, :] = self.Pos[HandNodeID, :] + NodeNewLocalTransform
                
    def Interpolate(self, method:str = "BSpline"):
        if method == "BSpline":
            if self.Pos.shape[1] <= 1:
                return
            for BoneID in range(self.Pos.shape[0]):
                # Interpolate Rotation
                currentRotCurve = self.Rot[BoneID]
                RotNanMask = np.max(np.isnan(currentRotCurve), axis=-1)
                if RotNanMask.any():
                    if RotNanMask.all():
                        raise ValueError(f"One of the bone with ID {BoneID} has no recorded Rotation key!")
                    InputRotFrames = np.where(np.logical_not(RotNanMask))[0]
                    if len(InputRotFrames) == 1:
                        self.Rot[BoneID,:] = self.Rot[BoneID,InputRotFrames[0]]
                    else:
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
                # for frameID in range(self.FrameCount):
                ParentRotation = Rotation.from_quat(self.Rot[ParentBoneID])
                LocalRotation = Rotation.from_quat(self.Rot[CurrentBoneID])
                GlobalRotation = ParentRotation * LocalRotation
                self.Rot[CurrentBoneID,] = GlobalRotation.as_quat(canonical=True)
                self.Pos[CurrentBoneID] = self.Pos[ParentBoneID] + ParentRotation.apply(self.Pos[CurrentBoneID])
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

def ProcessAnimFile(inputPath, outputPath):
    if os.path.exists(outputPath):
        return
    os.makedirs(os.path.dirname(outputPath), exist_ok=True)
    InputAnimation = GOHAnim(inputPath)
    # Record Positions For later IK
    if InputAnimation.IsBoneExist("foot3L") and InputAnimation.IsBoneExist("foot3R"):
        StartLFootPosition = InputAnimation.GetNodePosByName("foot3L")
        StartRFootPosition = InputAnimation.GetNodePosByName("foot3R")

    LH_IK_TargetList = ["Hand_rot1L", "Hand3L", "left_hand"]
    for BoneName in LH_IK_TargetList:
        if InputAnimation.IsBoneExist(BoneName):
            IK_L_HandName = BoneName
            break
    else:
        IK_L_HandName = None
    
    if IK_L_HandName != None:
        StartLHandPosition = InputAnimation.GetNodePosByName(IK_L_HandName)

    RH_IK_TargetList = ["Hand_rot1R", "Hand3R", "right_hand"]
    for BoneName in RH_IK_TargetList:
        if InputAnimation.IsBoneExist(BoneName):
            IK_R_HandName = BoneName
            break
    else:
        IK_R_HandName = None

    if IK_R_HandName != None:
        StartRHandPosition = InputAnimation.GetNodePosByName(IK_R_HandName)

    # Set Fixed offset
    ## LowerBody
    # InputAnimation.ApplyLocalPosIfExist('Body', np.array((0,0,-19.9225))) # Body should be free to move
    InputAnimation.ApplyLocalPosIfExist('foot1R', np.array((-0.1435,1.7855,-0.489)))
    InputAnimation.ApplyLocalPosIfExist('foot2R', np.array((9.25,0,0)))
    InputAnimation.ApplyLocalPosIfExist('foot3R', np.array((10.5,0,0)))
    InputAnimation.ApplyLocalPosIfExist('Bone03', np.array((10,0.25,0)))
    InputAnimation.ApplyLocalPosIfExist('Bone05', np.array((2.95,0,0)))
    
    InputAnimation.ApplyLocalPosIfExist('foot1L', np.array((-0.1435,-1.7855,-0.489)))
    InputAnimation.ApplyLocalPosIfExist('foot2L', np.array((9.25,0,0)))
    InputAnimation.ApplyLocalPosIfExist('foot3L', np.array((10.5,0,0)))
    InputAnimation.ApplyLocalPosIfExist('Bone06', np.array((10,0.25,0)))
    InputAnimation.ApplyLocalPosIfExist('Bone07', np.array((2.95,0,0)))
    

    ## UpperBody
    InputAnimation.ApplyLocalPosIfExist('IK_LeftRight', np.array((2.075,0.0375,0)))
    InputAnimation.ApplyLocalPosIfExist('IK_UpDown', np.array((0,0,-1.668)))
    InputAnimation.ApplyLocalPosIfExist('Head', np.array((-1.596, 5.411, 0)))

    InputAnimation.ApplyLocalPosIfExist('Clavicle_right', np.array((-1.425, 4.7775, -0.3945)))
    InputAnimation.ApplyLocalPosIfExist('Hand1R', np.array((0.05, -0.75, -1.96)))
    InputAnimation.ApplyLocalPosIfExist('Hand2R', np.array((5.0, 0, 0)))
    InputAnimation.ApplyLocalPosIfExist('Hand3R', np.array((4.73, 0, 0)))
    InputAnimation.ApplyLocalPosIfExist('Hand_rot1R', np.array((4.73, 0, 0)))
    InputAnimation.ApplyLocalPosIfExist('right_hand', np.array((5.735, -0.125, 0.25)))

    InputAnimation.ApplyLocalPosIfExist('Palm1R', np.array((0, -0.36, 0)))
    InputAnimation.ApplyLocalPosIfExist('Palm2R', np.array((0, 0, 1.285)))
    InputAnimation.ApplyLocalPosIfExist('Palm2R_hide', np.array((0, 0, 1.285)))
    InputAnimation.ApplyLocalPosIfExist('Palm3R', np.array((0.579, 0, 0)))
    InputAnimation.ApplyLocalPosIfExist('Palm3R_hide', np.array((0.579, 0, 0)))
    InputAnimation.ApplyLocalPosIfExist('Palm4R_hide', np.array((0.512, 0, 0)))
    InputAnimation.ApplyLocalPosIfExist('IK Chain07', np.array((0, 0, 2.7)))

    InputAnimation.ApplyLocalPosIfExist('Clavicle_left', np.array((-1.425, 4.7775, 0.3945)))
    InputAnimation.ApplyLocalPosIfExist('Hand1L', np.array((0.05, -0.75, 1.96)))
    InputAnimation.ApplyLocalPosIfExist('Hand2L', np.array((5.0, 0, 0)))
    InputAnimation.ApplyLocalPosIfExist('Hand3L', np.array((4.73, 0, 0)))
    InputAnimation.ApplyLocalPosIfExist('Hand_rot1L', np.array((4.73, 0, 0)))
    InputAnimation.ApplyLocalPosIfExist('left_hand', np.array((5.735, -0.125, -0.25)))

    InputAnimation.ApplyLocalPosIfExist('Palm1L', np.array((0, -0.36, 0)))
    InputAnimation.ApplyLocalPosIfExist('Palm2L', np.array((0, 0, 1.285)))
    InputAnimation.ApplyLocalPosIfExist('Palm2L_hide', np.array((0, 0, 1.285)))
    InputAnimation.ApplyLocalPosIfExist('Palm3L', np.array((0.579, 0, 0)))
    InputAnimation.ApplyLocalPosIfExist('Palm3L_hide', np.array((0.579, 0, 0)))
    InputAnimation.ApplyLocalPosIfExist('Palm4L_hide', np.array((0.512, 0, 0)))
    InputAnimation.ApplyLocalPosIfExist('IK Chain08', np.array((0, 0, 2.7)))

    # IK
    ## Initial
    if InputAnimation.IsBoneExist("foot3L") and InputAnimation.IsBoneExist("foot3R"):
        CurrentLFootPosition = InputAnimation.GetNodePosByName("foot3L")
        CurrentRFootPosition = InputAnimation.GetNodePosByName("foot3R")
        OverallPosOffset = ((StartLFootPosition + StartRFootPosition) - (CurrentLFootPosition + CurrentRFootPosition)) / 2
        InputAnimation.ApplyOverallPosOffset(OverallPosOffset, ExcludeBones=["BASIS"])
    ## Full
    if InputAnimation.IsBoneExist("foot3L") and InputAnimation.IsBoneExist("foot3R"):
        InputAnimation.IKToPosition('foot1L','foot2L','foot3L', StartLFootPosition, ElbowPositive = False)
        InputAnimation.IKToPosition('foot1R','foot2R','foot3R', StartRFootPosition, ElbowPositive = False)

    if InputAnimation.IsBoneExist('Hand1L') and InputAnimation.IsBoneExist('Hand2L') and IK_L_HandName != None:
        InputAnimation.IKToPosition('Hand1L','Hand2L',IK_L_HandName, StartLHandPosition, ElbowPositive = True, HandBoneApplyNameList=LH_IK_TargetList)
    if InputAnimation.IsBoneExist('Hand1R') and InputAnimation.IsBoneExist('Hand2R') and IK_R_HandName != None:
        InputAnimation.IKToPosition('Hand1R','Hand2R',IK_R_HandName, StartRHandPosition, ElbowPositive = True, HandBoneApplyNameList=RH_IK_TargetList)


    InputAnimation.ExportFrameToCSV(0, "After.csv")
    # ## Write
    InputAnimation.write(outputPath)

def TryProcessAnimFile(*Params):
    try:
        ProcessAnimFile(*Params)
    except Exception as e:
        print(f"Warning: {e}! On file [{Params[0]}]")


if __name__== "__main__":
    # # # # DEBUG
    # TestInputAnimPath = r"D:\GAMES\Modding\Python_MaxScript_Workdir\GFA_Model_Weight_Transfer\AnimationEdit\animation\human\death\die_crouch\die_crouch_01a.anm"
    # TestOutputAnimPath = r"D:\GAMES\Modding\Python_MaxScript_Workdir\GFA_Model_Weight_Transfer\AnimationEdit\TEST.anm"
    # if os.path.isfile(TestOutputAnimPath):
    #     os.remove(TestOutputAnimPath)
    # InputAnim = GOHAnim(TestInputAnimPath)
    # InputAnim.ExportFrameToCSV(0, r"D:\GAMES\Modding\Python_MaxScript_Workdir\GFA_Model_Weight_Transfer\AnimationEdit\Before.csv")
    # # # InputAnim.write(r"D:\GAMES\Modding\Python_MaxScript_Workdir\GFA_Model_Weight_Transfer\AnimationEdit\anim_idle_02_Refit.anm")
    # ProcessAnimFile(TestInputAnimPath, TestOutputAnimPath)
    # GOHAnim(TestOutputAnimPath).ExportFrameToCSV(0, r"D:\GAMES\Modding\Python_MaxScript_Workdir\GFA_Model_Weight_Transfer\AnimationEdit\After.csv")

    # # Run
    WorkerPool = Pool(32)
    InputRoot = r"D:\GAMES\Modding\Python_MaxScript_Workdir\GFA_Model_Weight_Transfer\AnimationEdit\animation"
    OutputRoot = r"D:\GAMES\Modding\Python_MaxScript_Workdir\GFA_Model_Weight_Transfer\AnimationEdit\animation_patch\animation"
    TaskList = list()
    for root, dirs, files in os.walk(InputRoot):
        for file in files:
            if file.endswith(".anm"):
                inputPath = os.path.join(root, file)
                outputPath = os.path.join(OutputRoot, os.path.relpath(inputPath, InputRoot))
                TaskList.append([inputPath, outputPath])
            else:
                print(f"Strangefile is not anm: [{os.path.join(root, file)}]")
    # [TryProcessAnimFile(*Task) for Task in TaskList]
    WorkerPool.starmap(TryProcessAnimFile, TaskList)