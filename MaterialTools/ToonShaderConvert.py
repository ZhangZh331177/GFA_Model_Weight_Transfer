import os

def GetFirstObject(InputString):
    InDoubleQuote = False
    InSingleQuote = False
    for CharID in range(len(InputString)):
        if InputString[CharID] == '"':
            InDoubleQuote = (not InDoubleQuote)
        elif InputString[CharID] == "'":
            InSingleQuote = (not InSingleQuote)
        elif InputString[CharID] == "{":
            if (not InDoubleQuote) and (not InSingleQuote):
                startID = CharID
                break
    else:
        raise ValueError("Found No Object in input string!")
    
    InDoubleQuote = False
    InSingleQuote = False
    BraceCount = 1
    for CharID in range(startID+1, len(InputString)):
        if InputString[CharID] == '"':
            InDoubleQuote = (not InDoubleQuote)
        elif InputString[CharID] == "'":
            InSingleQuote = (not InSingleQuote)
        elif InputString[CharID] == "{":
            if (not InDoubleQuote) and (not InSingleQuote):
                BraceCount += 1
        elif InputString[CharID] == "}":
            if (not InDoubleQuote) and (not InSingleQuote):
                BraceCount -= 1
                if BraceCount == 0:
                    endID = CharID + 1
                    break
    else:
        raise ValueError("Object not ended in input string!")
    
    return (startID, endID)
        
        
    


class MTLObject:
    def __init__(self, Key:str, Value:str|None, ChildList:list):
        self.Key = Key
        self.Value = Value
        self.ChildList = ChildList

    @staticmethod
    def initFromMTLStr(MTLStr:str):
        MTLStr = MTLStr.strip()
        # Check Format
        if not MTLStr.startswith("{") and MTLStr.endswith("}"):
            raise NotImplementedError("An subobject do not starts with '{' and ends with '}'!")
        # Trim '{' and '}'
        MTLStr = MTLStr[1:-1].strip()
        # Seperate strings
        MTL_KVPair_Str = MTLStr.split("{", maxsplit=1)[0]
        MTL_Childs_Str = MTLStr[len(MTL_KVPair_Str):]

        MTL_KVPair_Str = MTL_KVPair_Str.strip()
        MTL_Childs_Str = MTL_Childs_Str.strip()
        
        # K-V
        if ' ' in MTL_KVPair_Str:
            Init_Key, Init_Value = MTL_KVPair_Str.split(' ', maxsplit=1)
            Init_Key = Init_Key.strip()
            Init_Value = Init_Value.strip()
        else:
            Init_Key = MTL_KVPair_Str.strip()
            Init_Value = None
        
        # Children
        Init_ChildList = list()
        if "{" in MTL_Childs_Str:
            while "{" in MTL_Childs_Str:
                ChildStart, ChildEnd = GetFirstObject(MTL_Childs_Str)
                Init_ChildList.append(MTLObject.initFromMTLStr(MTL_Childs_Str[ChildStart: ChildEnd]))
                MTL_Childs_Str = MTL_Childs_Str[ChildEnd:].strip()
            if MTL_Childs_Str != "":
                raise ValueError("MTL_Childs string is not empty after extracting all childs!")
        
        return MTLObject(Init_Key, Init_Value, Init_ChildList)

    def GetChildByName(self, ChildName:str):
        ReturnList = list()
        if self.ChildList != None:
            for Child in self.ChildList:
                if Child.Key == ChildName:
                    ReturnList.append(Child)
        if len(ReturnList) > 1:
            raise ValueError("Multiple Children with Same Key!")
        elif len(ReturnList) == 1:
            return ReturnList[0]
        else:
            return None

    def AddChild(self, Child):
        self.ChildList.append(Child)
    
    def HasChild(self, Key):
        return self.GetChildByName(Key) != None

    def SetChildValue(self, Key, Value):
        TargetChild = self.GetChildByName(Key)
        if TargetChild != None:
            TargetChild.Value = Value
        else:
            self.AddChild(MTLObject(Key, Value, []))

    def ToMTLString(self, IndentLevel = 0):
        OutputString = (("\t" * IndentLevel) + "{" + self.Key)
        if self.Value is not None:
            OutputString += (" " + self.Value)
        if not self.ChildList:
            OutputString += "}\n"
        else:
            OutputString += "\n"
            for Child in self.ChildList:
                OutputString += Child.ToMTLString(IndentLevel = IndentLevel + 1)
            OutputString += (("\t" * IndentLevel) + "}\n")
        
        return OutputString

def GetMTLType(MTLObject):
    TAGDict = {
        "DIFF_HAIR": ["HAIR"],
        "DIFF_FACE": ["FACE", "EYE", "HEAD"],
        "DIFF_BODY": ["BODY", "SKIN"],
        "DIFF_CLOTH": ["SUIT", "CLOTH", "UNIFORM", "PANTY", "DRESS", "OUTFIT", "GLASSES", "GRENADE", "WEAPON", "SWORD"]
    }

    DiffuseObj = MTLObject.GetChildByName("diffuse")
    if DiffuseObj == None:
        return "DIFF_NONE"
    
    DiffuseName = DiffuseObj.Value
    if DiffuseName== None:
        return "DIFF_NONE"
    
    for TagTypeName, TagList in TAGDict.items():
        for Tag in TagList:
            if Tag in DiffuseName.upper():
                return TagTypeName
            
    else:
        return "DIFF_OTHER"


def ConvertMTL(InputPath, OutputPath):

    with open(InputPath) as InputMTLFile:
        InputMTLObj = MTLObject.initFromMTLStr(InputMTLFile.read())
        MTLType = GetMTLType(InputMTLObj)
        if MTLType == "DIFF_HAIR":
            InputMTLObj.Value = "bump"
            if not InputMTLObj.HasChild("bump"):
                InputMTLObj.SetChildValue("bump", '"$/dummyTex/normal"')
            if not InputMTLObj.HasChild("specular"):
                InputMTLObj.SetChildValue("specular", '"$/dummyTex/black"')
            InputMTLObj.SetChildValue("blend", 'test')
            InputMTLObj.SetChildValue("full_specular", None)
        elif MTLType == "DIFF_FACE":
            InputMTLObj.Value = "bump"
            if not InputMTLObj.HasChild("bump"):
                InputMTLObj.SetChildValue("bump", '"$/dummyTex/normal"')
            if not InputMTLObj.HasChild("specular"):
                InputMTLObj.SetChildValue("specular", '"$/dummyTex/black"')
            if not InputMTLObj.HasChild("blend"):
                InputMTLObj.SetChildValue("blend", 'none')
            InputMTLObj.SetChildValue("full_specular", None)
        elif MTLType == "DIFF_CLOTH":
            InputMTLObj.Value = "bump"
            if not InputMTLObj.HasChild("bump"):
                InputMTLObj.SetChildValue("bump", '"$/dummyTex/normal"')
            if not InputMTLObj.HasChild("specular"):
                InputMTLObj.SetChildValue("specular", '"$/dummyTex/black"')
            if not InputMTLObj.HasChild("height"):
                InputMTLObj.SetChildValue("height", '"$/envmap/env"')
            if not InputMTLObj.HasChild("blend"):
                InputMTLObj.SetChildValue("blend", 'none')
            InputMTLObj.SetChildValue("full_specular", None)
        elif MTLType == "DIFF_BODY":
            InputMTLObj.Value = "bump"
            if not InputMTLObj.HasChild("bump"):
                InputMTLObj.SetChildValue("bump", '"$/dummyTex/normal"')
            if not InputMTLObj.HasChild("specular"):
                InputMTLObj.SetChildValue("specular", '"$/dummyTex/black"')
            if not InputMTLObj.HasChild("height"):
                InputMTLObj.SetChildValue("height", '"$/envmap/env"')
            if not InputMTLObj.HasChild("blend"):
                InputMTLObj.SetChildValue("blend", 'none')
            InputMTLObj.SetChildValue("full_specular", None)
            
        elif MTLType == "DIFF_NONE" or MTLType == "DIFF_OTHER":
            pass
        else:
            raise ValueError("UNKNOWN MAT TYPE!!!!!!")
        
        with open(OutputPath, "w") as OutFile:
            OutFile.write(InputMTLObj.ToMTLString())


inputDir = r"D:\GAMES\Modding\Python_MaxScript_Workdir\GFA_Model_Weight_Transfer\MaterialTools\entity"
outputDir = r"D:\GAMES\Modding\Python_MaxScript_Workdir\GFA_Model_Weight_Transfer\MaterialTools\entity_patch"

for root, dirs, files in os.walk(inputDir):
    for file in files:
        if file.endswith(".mtl"):
            InputPath = os.path.join(root, file)
            InputRelPath = os.path.relpath(InputPath, inputDir)
            OutputPath = os.path.join(outputDir, InputRelPath)
            os.makedirs(os.path.dirname(OutputPath), exist_ok=True)
            ConvertMTL(InputPath, OutputPath)
