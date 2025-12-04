from pymxs import runtime as rt

# Run this script on Reference MaxFile once for Name avoidance.
Prefix = "GFA_MWT_SKE_"
for currentObject in rt.objects:
    if currentObject.name.startswith(Prefix):
        currentObject.name = currentObject.name[len(Prefix):]