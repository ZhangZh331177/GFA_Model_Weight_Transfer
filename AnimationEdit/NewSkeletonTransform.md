* LowerLegLength * 1.16
  * Bone06 - foot2L
  * foot3L - foot2L
  * Bone03 - foot2R
  * foot3R - foot2R
* UpperLegLength * 0.99
  * foot2R - foot1R
  * foot2L - foot1L
* PelvisWidth * 0.83
  * foot1R - foot1L
* LowerBody * 1.09
  * IK_LeftRight - Body
* Clavicle_LR * 0.78
  * Clavicle_left - IK_UpDown
  * Clavicle_right - IK_UpDown
* Neck * 0.75
  * Head - IK_UpDown
* ClavicleWidth * 0.43
  * Clavicle_left - Clavicle_right
* Hand1L * 1.05
  * Hand1L - Clavicle_left
* Hand1R * 0.91
  * Hand1R - Clavicle_right
* Hand2_LR * 0.80
  * Hand2R - Hand1R
  * Hand2L - Hand1L
* Hand3_LR * 0.90
  * Hand_rot1R - Hand2R
  * Hand3R - Hand2R
  * right_hand - Hand2R
  * Hand_rot1L - Hand2L
  * Hand3L - Hand2L
  * left_hand - Hand2L


* Reset All skeleton position by aligning new foot
  * Median (foot3L, foot3R)
  * Move All Bones