from pymxs import runtime as rt

# Run this script on Reference MaxFile once for Name avoidance.

for currentObject in rt.objects:
    currentObject.name = "GFA_MWT_SKE_" + currentObject.name