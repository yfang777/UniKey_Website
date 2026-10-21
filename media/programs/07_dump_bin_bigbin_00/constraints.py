from __future__ import annotations

import numpy as np

_pos_cost = globals().get("_pos_cost")
_samedir_cost = globals().get("_samedir_cost")
_unit = globals().get("_unit")


# 1 = GRASP/CLOSE, -1 = RELEASE/OPEN, 0 = MOVE/CONSTRAIN
grasp_stage = [
    0,  # 1. Move above the table-bin rim
    0,  # 2. Move to the rim
    1,  # 3. Grasp the table bin
    0,  # 4. Lift the table bin
    0,  # 5. Move it above the big bin
    0,  # 6. Turn it upside down to empty it
]
num_stages = len(grasp_stage)
grasp_keypoints = [-1, -1, 6, -1, -1, -1]


EE = 0
BIG_BIN_CENTER = 1
TABLE_BIN_CENTER = 3
TABLE_BIN_TOP = 4
TABLE_BIN_GRASP = 6
EE_LEFT = -2
EE_RIGHT = -1

APPROACH_HEIGHT = 0.08
LIFT_HEIGHT = 0.25
POUR_OFFSET_Z = 0.25


def _table_bin_up(keypoints):
    return _unit(keypoints[TABLE_BIN_TOP] - keypoints[TABLE_BIN_CENTER])


def _gripper_bottom_to_top(keypoints):
    finger_center = (keypoints[EE_LEFT] + keypoints[EE_RIGHT]) / 2.0
    return _unit(finger_center - keypoints[EE])


def stage1_constraint1(keypoints):
    target = keypoints[TABLE_BIN_GRASP] + np.array([0.0, 0.0, APPROACH_HEIGHT])
    return _pos_cost(keypoints[EE], target)


def stage1_constraint2(keypoints):
    return _samedir_cost(
        _gripper_bottom_to_top(keypoints),
        np.array([0.0, 0.0, 1.0]),
    )


def stage2_constraint1(keypoints):
    return _pos_cost(keypoints[EE], keypoints[TABLE_BIN_GRASP])


def stage2_constraint2(keypoints):
    return _samedir_cost(
        _gripper_bottom_to_top(keypoints),
        np.array([0.0, 0.0, 1.0]),
    )


def stage4_constraint1(keypoints):
    target = np.array(
        [keypoints[TABLE_BIN_CENTER][0], keypoints[TABLE_BIN_CENTER][1], LIFT_HEIGHT]
    )
    return _pos_cost(keypoints[TABLE_BIN_CENTER], target)

def stage4_constraint2(keypoints):
    return _samedir_cost(_table_bin_up(keypoints), np.array([0.0, 0.0, 1.0]))


def stage5_constraint1(keypoints):
    target = keypoints[BIG_BIN_CENTER] + np.array([0.0, -0.07, POUR_OFFSET_Z])
    return _pos_cost(keypoints[TABLE_BIN_CENTER], target)

def stage5_constraint2(keypoints):
    return _samedir_cost(_gripper_bottom_to_top(keypoints), np.array([0.0, 0., 1.0]))


def stage6_constraint1(keypoints):
    
    target = keypoints[BIG_BIN_CENTER] + np.array([0.0, -0.07, POUR_OFFSET_Z])
    return _pos_cost(keypoints[TABLE_BIN_CENTER], target)

def stage6_constraint2(keypoints):
    return _samedir_cost(_gripper_bottom_to_top(keypoints), np.array([0.0, 1.0, -0.15])) * 10
