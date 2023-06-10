from numba import njit
import numpy as np
import math
from typing import Tuple

eps = 1e-8


@njit(cache=True)
def from_translation(translation_vector: np.ndarray, translation: np.ndarray) -> None:
    translation[:3, 3] = translation_vector


@njit(cache=True)
def from_scale(scale_vector: np.ndarray, scale: np.ndarray) -> None:
    scale[0, 0] = scale_vector[0]
    scale[1, 1] = scale_vector[1]
    scale[2, 2] = scale_vector[2]


# Implementation from: https://github.com/adamlwgriffiths/Pyrr/blob/f6c8698c48a75f3fb7ad0d47d0ce80a04f87ba2f/pyrr
# /matrix33.py#L108
@njit(cache=True)
def from_quaternion(quat: np.ndarray, rotation: np.ndarray) -> None:
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
def normalize(v: np.ndarray) -> np.ndarray:
    squared_sum = 0.0
    for i in range(len(v)):
        squared_sum += v[i] * v[i]
    return v / np.sqrt(squared_sum)


@njit(cache=True)
def clip(x: np.float32, min_val: np.float32, max_val: np.float32) -> float:
    return min(max(x, min_val), max_val)


# Implementation from: https://github.com/adamlwgriffiths/Pyrr/blob/f6c8698c48a75f3fb7ad0d47d0ce80a04f87ba2f/pyrr
# /quaternion.py#L231
@njit(cache=True)
def slerp(quat1: np.ndarray, quat2: np.ndarray, timestamp: float, timestamp_1: float, timestamp_2: float) -> np.ndarray:
    slerp_amount = (timestamp - timestamp_1) / (timestamp_2 - timestamp_1)
    t = clip(np.float32(slerp_amount), np.float32(0.0), np.float32(1.0))

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
def lerp(vector_1: np.ndarray, vector_2: np.ndarray, timestamp: float, timestamp_1: float,
         timestamp_2: float) -> np.ndarray:
    lerp_amount = (timestamp - timestamp_1) / (timestamp_2 - timestamp_1)
    lerp_amount = clip(np.float32(lerp_amount), np.float32(0.0), np.float32(1.0))

    return vector_1 * (1 - lerp_amount) + vector_2 * lerp_amount


@njit(cache=True)
def quat_mult(q1: np.ndarray, q0: np.ndarray) -> np.ndarray:
    return np.array([q0[0] * q1[0] - q0[1] * q1[1] - q0[2] * q1[2] - q0[3] * q1[3],
                     q0[0] * q1[1] + q0[1] * q1[0] - q0[2] * q1[3] + q0[3] * q1[2],
                     q0[0] * q1[2] + q0[1] * q1[3] + q0[2] * q1[0] - q0[3] * q1[1],
                     q0[0] * q1[3] - q0[1] * q1[2] + q0[2] * q1[1] + q0[3] * q1[0]])


@njit(cache=True)
def quat_abs(quat: np.ndarray) -> np.ndarray:
    if quat[0] < 0:
        quat = - quat
    return quat


@njit(cache=True)
def quat_norm(quat: np.ndarray) -> np.ndarray:
    return quat / (np.sqrt(quat[0] ** 2 + quat[1] ** 2 + quat[2] ** 2 + quat[3] ** 2) + eps)


@njit(cache=True)
def quat_log(quat: np.ndarray) -> np.ndarray:
    length = np.sqrt(quat[1] ** 2 + quat[2] ** 2 + quat[3] ** 2)

    if length < eps:
        return np.array([quat[1], quat[2], quat[3]])
    else:
        if quat[0] < -1:
            quat[0] = -1
        elif quat[0] > 1:
            quat[0] = 1

        angle = np.arccos(quat[0])
        return angle * np.array([quat[1], quat[2], quat[3]]) / length


@njit(cache=True)
def quat_exp(vec3: np.ndarray) -> np.ndarray:
    angle = np.sqrt(vec3[0] ** 2 + vec3[1] ** 2 + vec3[2] ** 2)
    if angle < eps:
        return quat_norm(np.array([1, vec3[0], vec3[1], vec3[2]]))
    else:
        c = np.cos(angle)
        s = np.sin(angle) / angle
        return np.array([c, vec3[0] * s, vec3[1] * s, vec3[2] * s])


@njit(cache=True)
def quat_to_scaled_angle_axis(quat: np.ndarray) -> np.ndarray:
    return 2 * quat_log(quat)


@njit(cache=True)
def quat_from_scaled_angle_axis(vec3: np.ndarray) -> np.ndarray:
    return quat_exp(vec3 / 2)


@njit(cache=True)
def quat_inv(quat: np.ndarray) -> np.ndarray:
    return np.array([quat[0], - quat[1], -quat[2], -quat[3]])


@njit(cache=True)
def return_coefficients(t: float) -> Tuple[float, float, float]:
    w1 = 3 * t ** 2 - 2 * t ** 3
    w2 = t ** 3 - 2 * t ** 2 + t
    w3 = t ** 3 - t ** 2
    return w1, w2, w3


@njit(cache=True)
def hermite_translation(p0: np.ndarray, p1: np.ndarray, v0: np.ndarray, v1: np.ndarray, timestamp: float) -> np.ndarray:
    p1_sub_p0 = p1 - p0
    w1, w2, w3 = return_coefficients(timestamp)

    return w1 * p1_sub_p0 + w2 * v0 + w3 * v1 + p0


@njit(cache=True)
def hermite_rotation(r0: np.ndarray, r1: np.ndarray, v0: np.ndarray, v1: np.ndarray, timestamp: float) -> np.ndarray:
    w1, w2, w3 = return_coefficients(timestamp)

    r1_sub_r0 = quat_to_scaled_angle_axis(quat_abs(quat_mult(r1, quat_inv(r0))))

    return quat_mult(quat_from_scaled_angle_axis(w1 * r1_sub_r0 + w2 * v0 + w3 * v1), r0)


@njit(cache=True)
def hermite_scale(s0: np.ndarray, s1: np.ndarray, v0: np.ndarray, v1: np.ndarray, timestamp: float) -> np.ndarray:
    s1_sub_s0 = np.log(s1 / s0)
    w1, w2, w3 = return_coefficients(timestamp)

    return np.exp(w1 * s1_sub_s0 + w2 * v0 + w3 * v1) * s0


@njit(cache=True)
def calculate_translation_tangents(p0: np.ndarray, p1: np.ndarray,
                                   p2: np.ndarray, p3: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    translation_v1 = ((p1 - p0) + (p2 - p1)) / 2
    translation_v2 = ((p2 - p1) + (p3 - p2)) / 2

    return translation_v1, translation_v2


@njit(cache=True)
def calculate_rotation_tangents(r0: np.ndarray, r1: np.ndarray,
                                r2: np.ndarray, r3: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    r1_sub_r0 = quat_to_scaled_angle_axis(quat_abs(quat_mult(r1, quat_inv(r0))))
    r2_sub_r1 = quat_to_scaled_angle_axis(quat_abs(quat_mult(r2, quat_inv(r1))))
    r3_sub_r2 = quat_to_scaled_angle_axis(quat_abs(quat_mult(r3, quat_inv(r2))))

    rotation_v1 = (r1_sub_r0 + r2_sub_r1) / 2
    rotation_v2 = (r2_sub_r1 + r3_sub_r2) / 2

    return rotation_v1, rotation_v2


@njit(cache=True)
def calculate_scale_tangents(s0: np.ndarray, s1: np.ndarray,
                             s2: np.ndarray, s3: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    s1_sub_s0 = np.log(s1 / s0)
    s2_sub_s1 = np.log(s2 / s1)
    s3_sub_s2 = np.log(s3 / s2)

    scale_v1 = (s1_sub_s0 + s2_sub_s1) / 2
    scale_v2 = (s2_sub_s1 + s3_sub_s2) / 2

    return scale_v1, scale_v2


@njit(cache=True)
def calculate_translation_tangent(p0: np.ndarray, p1: np.ndarray,
                                  t0: float, t1: float) -> Tuple[np.ndarray, np.ndarray]:
    return (p1 - p0) / (t1 - t0)


@njit(cache=True)
def calculate_rotation_tangent(r0: np.ndarray, r1: np.ndarray, t0: float, t1: float) -> Tuple[np.ndarray, np.ndarray]:
    r1_sub_r0 = quat_to_scaled_angle_axis(quat_abs(quat_mult(r1, quat_inv(r0))))
    return r1_sub_r0 / (t1 - t0)


@njit(cache=True)
def calculate_scale_tangent(s0: np.ndarray, s1: np.ndarray,
                            t0: np.ndarray, t1: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    s1_sub_s0 = np.log(s1 / s0)
    return s1_sub_s0 / (t1 - t0)
