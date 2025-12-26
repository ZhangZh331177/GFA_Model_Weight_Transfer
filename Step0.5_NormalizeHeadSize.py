from pymxs import runtime as rt

def GetNodeByNameRaiser(InputNodeName):
    TargetNode = rt.getNodeByName(InputNodeName)
    if TargetNode == None:
        raise ValueError("Trying to GetNodeByName on an Unknown Name: [" + InputNodeName + "]!")
    else:
        return TargetNode

def VecDot(PointA, PointB):
    return (PointA.x * PointB.x) + (PointA.y * PointB.y) + (PointA.z * PointB.z)

def VecNorm(Point):
    return (Point.x ** 2 + Point.y ** 2 + Point.z ** 2) ** 0.5

### Normalize Head Size here
LeftEyeName = "Eye_L"
RightEyeName = "Eye_R"
NeckName = "Neck"

LeftShoulderName = "ShoulderP_L"
RightShoulderName = "ShoulderP_R"
LeftFootName = "Ankle_L"
RightFootName = "Ankle_R"


LeftEyePos = GetNodeByNameRaiser(LeftEyeName).pos
RightEyePos = GetNodeByNameRaiser(RightEyeName).pos
NeckPos = GetNodeByNameRaiser(NeckName).pos
LeftShoulderPos = GetNodeByNameRaiser(LeftShoulderName).pos
RightShoulderPos = GetNodeByNameRaiser(RightShoulderName).pos
LeftFootPos = GetNodeByNameRaiser(LeftFootName).pos
RightFootPos = GetNodeByNameRaiser(RightFootName).pos

#### Head size factors
BodyVector = ((LeftShoulderPos + RightShoulderPos) - (LeftFootPos + RightFootPos)) / 2.0 #[0,-0.174142,-50.6248]
BodyDistance = VecNorm(BodyVector) # 50.62509951077789

EyeLRVector = LeftEyePos - RightEyePos
EyeLRDistance = VecNorm(EyeLRVector) # 2.11018
EyeLRRatio = EyeLRDistance / BodyDistance
EyeLRExpectedRatio = 0.041682486 # 2.11018 / 50.62509951077789
RatioOffsetByEyeLR = EyeLRExpectedRatio / EyeLRRatio

EyeNeckVector = ((LeftEyePos + RightEyePos) / 2.0) - NeckPos #[0,-2.38843,5.42931]
EyeNeckDistanceOnBodyDirection = abs(VecDot(EyeNeckVector, BodyVector)) / VecNorm(BodyVector) # 5.421062073221453
EyeNeckRatio = EyeNeckDistanceOnBodyDirection / BodyDistance
EyeNeckExpectedRatio = 0.1070825 # 5.421062073221453 / 50.62509951077789
RatioOffsetByEyeNeck = EyeNeckExpectedRatio / EyeNeckRatio

#### Resize Head
RatioOffset = (RatioOffsetByEyeLR * RatioOffsetByEyeNeck) ** (1.0/2.0)
rt.scale(GetNodeByNameRaiser(NeckName), rt.Point3(RatioOffset, RatioOffset, RatioOffset))