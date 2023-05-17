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


# Implementation from: https://github.com/adamlwgriffiths/Pyrr/blob/f6c8698c48a75f3fb7ad0d47d0ce80a04f87ba2f/pyrr
# /matrix33.py#L108
@njit(cache=True)
def from_quaternion(quat, rotation):
    norm = math.sqrt(quat[0] ** 2 + quat[1] ** 2 + quat[2] ** 2 + quat[3] ** 2)
    if norm != 0:
        qx, qy, qz, qw = quat[0] / norm, quat[1] / norm, quat[2] / norm, quat[3] / norm
    else:
        qx, qy, qz, qw = quat[0], quat[1], quat[2], quat[3]

    sqw = qw ** 2
    sqx = qx ** 2
    sqy = qy ** 2
    sqz = qz ** 2
    qxy = qx * qy
    qzw = qz * qw
    qxz = qx * qz
    qyw = qy * qw
    qyz = qy * qz
    qxw = qx * qw

    invs = 1 / (sqx + sqy + sqz + sqw)
    m00 = (sqx - sqy - sqz + sqw) * invs
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
    squared_sum = 0.0
    for i in range(len(v)):
        squared_sum += v[i] * v[i]
    return v / np.sqrt(squared_sum)


@njit(cache=True)
def clip(x, min_val, max_val):
    return min(max(x, min_val), max_val)


# Implementation from: https://github.com/adamlwgriffiths/Pyrr/blob/f6c8698c48a75f3fb7ad0d47d0ce80a04f87ba2f/pyrr
# /quaternion.py#L231
@njit(cache=True)
def slerp(quat1, quat2, timestamp, timestamp_1, timestamp_2):

    slerp_amount = (timestamp - timestamp_1) / (timestamp_2 - timestamp_1)
    t = clip(slerp_amount, 0.0, 1.0)
    dot = 0.0
    for i in range(len(quat1)):
        dot += quat1[i] * quat2[i]

    if dot < 0.0:
        dot = -dot
        quat2 = -quat2

    if dot < 0.95:
        angle = np.arccos(dot)
        res = (quat1 * np.sin(angle * (1.0 - t)) + quat2 * np.sin(angle * t)) / np.sin(angle)

    else:
        res = normalize(quat1 * (1.0 - t) + quat2 * t)

    return res


@njit(cache=True)
def lerp(vector_1: np.ndarray, vector_2: np.ndarray, timestamp: float, timestamp_1: float, timestamp_2: float) -> np.ndarray:
    lerp_amount = (timestamp - timestamp_1) / (timestamp_2 - timestamp_1)
    lerp_amount = clip(lerp_amount, 0.0, 1.0)

    return vector_1 * (1 - lerp_amount) + vector_2 * lerp_amount
