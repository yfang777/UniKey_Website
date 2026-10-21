from __future__ import annotations

import numpy as np

_pos_cost = globals().get("_pos_cost")
_samedir_cost = globals().get("_samedir_cost")
_unit = globals().get("_unit")


# 1 = GRASP/CLOSE, -1 = RELEASE/OPEN, 0 = MOVE/CONSTRAIN
grasp_stage = [
    0,  # 1. Move above the bell
    1,  # 2. Close the gripper
    0,  # 3. Press the bell
]
num_stages = len(grasp_stage)
grasp_keypoints = [-1, 1, -1]


EE = 0
TARGET = 1
EE_LEFT = -2
EE_RIGHT = -1

APPROACH_HEIGHT = 0.08


def _gripper_bottom_to_top(keypoints):
    finger_center = (keypoints[EE_LEFT] + keypoints[EE_RIGHT]) / 2.0
    return _unit(finger_center - keypoints[EE])


def stage1_constraint1(keypoints):
    target = keypoints[TARGET] + np.array([0.0, 0.0, APPROACH_HEIGHT])
    return _pos_cost(keypoints[EE], target)


def stage1_constraint2(keypoints):
    return _samedir_cost(
        _gripper_bottom_to_top(keypoints),
        np.array([0.0, 0.0, 1.0]),
    )


def stage3_constraint1(keypoints):
    return _pos_cost(keypoints[EE], keypoints[TARGET] + np.array([0., 0., 0.05]))


def stage3_constraint2(keypoints):
    return _samedir_cost(
        _gripper_bottom_to_top(keypoints),
        np.array([0.0, 0.0, 1.0]),
    )
