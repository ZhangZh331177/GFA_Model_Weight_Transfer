
### Step 1. Blender Protocol

* Import with Blender MMD tools (UuuNyaa's forked version 2.10.3)
  * with option "Rename Bones To English" set to "Internal Dictionary"
* Export to FBX

### Step 2. 3dsmax Protocol

* Import the exported FBX file.
* Remove "rigidbodies" and all childs.
* Remove "joints" and all childs.
* Remove "ControlNode" and all childs.
* Remove all nodes endswith "_end"

### Aligning steps
* Overall scale and alignment
  * Scale the whole model by the height of shoulder (Clavicle_left:ShoulderP_L) (DONE)
  * Align the whole model center by the median point of first leg bones (LegD_L,LegD_R, Leg_L, Leg_R : foot1R, foot1L) (TODO)
* Lower body alignment
  * Align the rotation of the upper leg bones (LegD_L,LegD_R, Leg_L, Leg_R : foot1R, foot1L) (TODO)
  * Resize the upper leg to make the upper leg length same (TODO)
  * Same to the lower leg bones
  * Resize and rotate the foot according to parents, to make the foot's scale identical 1\:1\:1, rotation unchanged.
* Upperbody alignment
  * TODO

### Skeleton structure
* Root Body
* UpperLegR: ["foot1R", "foot2R"]
* UpperLegL: ["foot1L", "foot2L"]
* LowerLegR: ["foot2R", "foot3R"]
* LowerLegL: ["foot2L", "foot3L"]
* Spine: IK_LeftRight
* Chest: IK_UpDown

* Clavicle_left: Clavicle_left
* Clavicle_right: Clavicle_right
* UpperArmL: ["Hand1L", "Hand2L"]
* UpperArmR: ["Hand1R", "Hand2R"]
* LowerArmL: ["Hand2L", "Hand3L"]
* LowerArmR: ["Hand2R", "Hand3R"]
