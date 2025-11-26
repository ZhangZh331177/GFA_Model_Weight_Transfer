from pymxs import runtime as rt

def GetOrientation(left_pos, right_pos):
    # Cauculate the orientation
    diff = [r - l for l, r in zip(left_pos, right_pos)]
    abs_diff = [abs(x) for x in diff]
    lr_axis_idx = abs_diff.index(max(abs_diff))
    right_vec = [0, 0, 0]
    right_vec[lr_axis_idx] = 1 if diff[lr_axis_idx] > 0 else -1
    if lr_axis_idx == 2:
        head_vec = [0, 1, 0]
    else:
        head_vec = [0, 0, 1]
    face_vec = [
        head_vec[1]*right_vec[2] - head_vec[2]*right_vec[1],
        head_vec[2]*right_vec[0] - head_vec[0]*right_vec[2],
        head_vec[0]*right_vec[1] - head_vec[1]*right_vec[0]
    ]
    return face_vec, head_vec

def GetRotateAngle(face_vec_current, head_vec_current, face_vec_target, head_vec_target):
    # Cauculate the rotate angle, divided by two steps
    def cross(u, v):
        return [
            u[1] * v[2] - u[2] * v[1],
            u[2] * v[0] - u[0] * v[2],
            u[0] * v[1] - u[1] * v[0]
        ]
    def dot(u, v):
        return u[0]*v[0] + u[1]*v[1] + u[2]*v[2]
    def apply_simple_rotation(vec, rot_angle):
        if dot(rot_angle, rot_angle) == 180 * 180:
            return -vec
        elif dot(rot_angle, rot_angle) == 90 * 90:
            rot_angle = tuple(item // 90 for item in rot_angle)
            return cross(rot_angle, vec)
        else:
            return vec
    dot_product = dot(face_vec_current, face_vec_target)
    if dot_product == 1:
        step1_angle = (0, 0, 0)
    elif dot_product == -1:
        if face_vec_current[0] != 0:
            step1_angle = (0, 180, 0)
        else:
            step1_angle = (180, 0, 0)
    else:
        rot_face_vec = cross(face_vec_current, face_vec_target)
        # print(rot_face_vec)
        step1_angle = tuple(90 * item for item in rot_face_vec)
    head_vec_temp = apply_simple_rotation(head_vec_current, step1_angle)
    face_vec_temp = apply_simple_rotation(face_vec_current, step1_angle)
    if face_vec_temp != face_vec_target: print("ROTATE STEP 1 ERROR", face_vec_temp, face_vec_target)
    print(face_vec_temp, head_vec_temp)
    # ABOVE IS THE FIRST ROTATE
    if head_vec_temp == head_vec_target:
        step2_angle = (0, 0, 0)
    else:
        rot_axis = tuple(abs(item) for item in face_vec_temp)
        if dot(head_vec_temp, head_vec_target) == -1:
            step2_angle = tuple(180 * item for item in rot_axis)
        else:
            cross_prod = cross(head_vec_temp, head_vec_target)
            if dot(cross_prod, rot_axis) > 0:
                step2_angle = tuple(90 * item for item in rot_axis)
            else:
                step2_angle = tuple(-90 * item for item in rot_axis)
    return step1_angle, step2_angle

current_hands = [rt.getNodeByName('Wrist_L'), rt.getNodeByName('Wrist_R')]  # Hand bone of MMD
target_hands = [rt.getNodeByName('Hand3L'), rt.getNodeByName('Hand3R')]  # Hand bone of GOH
current_base = rt.getNodeByName('')  # Base bone of MMD
# target_base = rt.getNodeByName('')

# HOW TO GET THE POSITION?
current_hands_pos = []
target_hands_pos = []

face_vec_current, head_vec_current = GetOrientation(current_hands_pos[0], current_hands_pos[1])
face_vec_target, head_vec_target = GetOrientation(target_hands_pos[0], target_hands_pos[1])
step1_angle, step2_angle = GetRotateAngle(face_vec_current, head_vec_current, face_vec_target, head_vec_target)

rt.rotate(current_base, rt.eulerangles(step1_angle[0], step1_angle[1], step1_angle[2]))
rt.rotate(current_base, rt.eulerangles(step2_angle[0], step2_angle[1], step2_angle[2]))

