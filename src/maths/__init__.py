from numba import njit
import numpy as np
import math

@njit(cache=True)
def from_translation(translation_vector, translation):
    translation[:3, 3] = translation_vector

@njit(cache=True)
def from_scale(scale_vector, scale):
    scale[0, 0] = scale_vector[0]
    scale[1, 1] = scale_vector[1]
    scale[2, 2] = scale_vector[2]


# Implementation from: https://github.com/adamlwgriffiths/Pyrr/blob/f6c8698c48a75f3fb7ad0d47d0ce80a04f87ba2f/pyrr/matrix33.py#L108
@njit(cache=True)
def from_quaternion(quat, rotation):
    norm = math.sqrt(quat[0]**2 + quat[1]**2 + quat[2]**2 + quat[3]**2)
    if norm != 0:
        qx, qy, qz, qw = quat[0]/norm, quat[1]/norm, quat[2]/norm, quat[3]/norm
    else:
        qx, qy, qz, qw = quat[0], quat[1], quat[2], quat[3]

    sqw = qw**2
    sqx = qx**2
    sqy = qy**2
    sqz = qz**2
    qxy = qx * qy
    qzw = qz * qw
    qxz = qx * qz
    qyw = qy * qw
    qyz = qy * qz
    qxw = qx * qw

    invs = 1 / (sqx + sqy + sqz + sqw)
    m00 = ( sqx - sqy - sqz + sqw) * invs
    m11 = (-sqx + sqy - sqz + sqw) * invs
    m22 = (-sqx - sqy + sqz + sqw) * invs
    m10 = 2.0 * (qxy + qzw) * invs
    m01 = 2.0 * (qxy - qzw) * invs
    m20 = 2.0 * (qxz - qyw) * invs
    m02 = 2.0 * (qxz + qyw) * invs
    m21 = 2.0 * (qyz + qxw) * invs
    m12 = 2.0 * (qyz - qxw) * invs

    rotation[0, 0], rotation[0, 1], rotation[0, 2] = m00, m01, m02
    rotation[1, 0], rotation[1, 1], rotation[1, 2] = m10, m11, m12
    rotation[2, 0], rotation[2, 1], rotation[2, 2] = m20, m21, m22

@njit(cache=True)
def normalize(v):
    norm = np.linalg.norm(v)
    if norm == 0: 
        return v
    return v / norm

@njit(cache=True)
def clip(x, min_val, max_val):
    return min(max(x, min_val), max_val)

# Implementation from: https://github.com/adamlwgriffiths/Pyrr/blob/f6c8698c48a75f3fb7ad0d47d0ce80a04f87ba2f/pyrr/quaternion.py#L231
@njit(cache=True)
def slerp(quat1, quat2, t):

    t = clip(t, 0.0, 1.0)
    dot = np.dot(quat1, quat2)

    if dot < 0.0:
        dot = -dot
        quat3 = -quat2

    else:
        quat3 = quat2

    if dot < 0.95:
        angle = np.arccos(dot)
        res = (quat1 * np.sin(angle * (1.0 - t)) + quat3 * np.sin(angle * t)) / np.sin(angle)

    else:
        t = clip(t, 0.0, 1.0)
        res = normalize(quat1 * (1.0 - t) + quat2 * t)

    return res