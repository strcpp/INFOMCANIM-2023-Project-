from pyrr import Quaternion, Matrix44, Vector3, Vector4
from animation.bone import Bone
from typing import Optional
import numpy as np

# test
from dual_quaternions import DualQuaternion


class Animation:
    def __init__(self, name: str, duration: float, root_bone: Bone, root_transform: Matrix44) -> None:
        self.name = name
        self.duration = duration

        # storing bones as a node hierarchy, maybe it's better to store as a list instead? I think this is fine,
        # we have to traverse the hierarchy eventually anyway.
        self.root_bone = root_bone
        self.root_transform = root_transform

    def set_pose(self, timestamp: float, interpolation_method: str) -> None:
        t = timestamp % self.duration
        self.root_bone.set_pose(t, interpolation_method, self.root_transform)

    def get_sorted_joints(self):
        nodes = [(self.root_bone, Matrix44(np.identity(4, dtype=np.float32)))]
        joints = []

        while len(nodes) > 0:
            current_node, parent_transform = nodes.pop()
            if current_node.index > -1:
                #joint_matrix = np.transpose(current_node.inverse_bind_matrix)

                dq = current_node.dq * current_node.dq_bind.quaternion_conjugate()

                pair = (current_node.index, dq)
                joints.append(pair)

            nodes += list(zip(current_node.children, [current_node.local_transform for _ in current_node.children]))

        joints = list(map(lambda x: x[1], sorted(joints, key=lambda x: x[0])))
        #return np.array(joints, dtype='f4')
        return joints

    def get_sorted_dual_quaternion_joints(self):

        joints = self.get_sorted_joints()
        rs = []
        ts = []

        for _, dq in enumerate(joints):
            #_, r, t = Matrix44(m).decompose()

            #dq = DualQuaternion.from_quat_pose_array(np.array([r[3], r[0], r[1], r[2], t[0], t[1], t[2]]))

            rs.append(dq.q_r.q)
            ts.append(dq.q_d.q)

        return np.array(rs, dtype="f4"), np.array(ts, dtype="f4")

    # just testing to make sure we're loading the animation data correctly
    def assert_channels_not_empty(self, bone: Optional[Bone] = None) -> None:
        if bone is None:
            bone = self.root_bone

        if not bone.rotations:
            raise ValueError("Rotations channel is empty in bone: {}".format(bone.name))
        if not bone.scales:
            raise ValueError("Scales channel is empty in bone: {}".format(bone.name))
        if not bone.translations:
            raise ValueError("Translations channel is empty in bone: {}".format(bone.name))

        if bone.children:
            for child_bone in bone.children:
                self.assert_channels_not_empty(child_bone)
