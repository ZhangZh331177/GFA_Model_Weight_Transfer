from pymxs import runtime as rt

MMD_RootName = "GirlsFrontline AlvaDefault"
GOH_Clavicle_Name = "Clavicle_left"
MMD_Clavicle_Name = "ShoulderP_L"

GOH_Clavicle_Height = rt.getNodeByName(GOH_Clavicle_Name).pos.z
MMD_Clavicle_Height = rt.getNodeByName(MMD_Clavicle_Name).pos.z
scaleFactor = GOH_Clavicle_Height / MMD_Clavicle_Height

MMD_Root = rt.getNodeByName(MMD_RootName)
MMD_Root.scale = MMD_Root.scale * scaleFactor