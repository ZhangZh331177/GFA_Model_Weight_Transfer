from pymxs import runtime as rt
Prefix = "GFA_MWT_SKE_"
CSVPath = r"C:\Users\simon\Downloads\AnimationEdit\Before.csv"
with open(CSVPath) as inputCSV:
    for line in inputCSV:
        NodeNameStr, XStr, YStr, ZStr = line.split(",")
        NodeName = NodeNameStr.strip()
        PosX = float(XStr.strip())
        PosY = float(YStr.strip())
        PosZ = float(ZStr.strip())
        for currentObject in rt.objects:
            if currentObject.name[len(Prefix):].upper() == NodeName.upper():
                currentObject.pos = rt.Point3(PosX, PosY, PosZ)