from __future__ import annotations

import numpy as np

_orthogonal_cost = globals().get("_orthogonal_cost")
_pos_cost = globals().get("_pos_cost")
_samedir_cost = globals().get("_samedir_cost")
_unit = globals().get("_unit")


# 1 = GRASP, -1 = RELEASE, 0 = MOVE/CONSTRAIN
grasp_stage = [
    0,  # 1. Approach the hammer handle
    0,  # 2. Move to the handle grasp point
    1,  # 3. Grasp the hammer
    0,  # 4. Lift the hammer clear of the table
    0,  # 5. Move the hammer head above the block
    0,  # 6. Strike the block
]
num_stages = len(grasp_stage)
grasp_keypoints = [-1, -1, 1, -1, -1, -1]


EE = 0
EE_LEFT = -2
EE_RIGHT = -1

HAMMER_GRASP = 1
HAMMER_HANDLE_END = 2
HAMMER_HEAD = 3
BLOCK_TOP = 5

APPROACH_HEIGHT = 0.08
GRASP_HEIGHT = 0.0
CLEARANCE_HEIGHT = 0.14
PRE_STRIKE_HEIGHT = 0.07


def _hammer_shaft_axis(keypoints):
    return _unit(keypoints[HAMMER_GRASP] - keypoints[HAMMER_HANDLE_END])


def _gripper_bottom_to_top(keypoints):
    finger_center = (keypoints[EE_LEFT] + keypoints[EE_RIGHT]) / 2.0
    return _unit(finger_center - keypoints[EE])


def _gripper_left_to_right(keypoints):
    return _unit(keypoints[EE_RIGHT] - keypoints[EE_LEFT])


def stage1_constraint1(keypoints):
    target = keypoints[HAMMER_GRASP] + np.array([0.0, 0.0, APPROACH_HEIGHT])
    return _pos_cost(keypoints[EE], target)


def stage1_constraint2(keypoints):
    return _orthogonal_cost(_gripper_left_to_right(keypoints), _hammer_shaft_axis(keypoints))


def stage1_constraint3(keypoints):
    return _samedir_cost(_gripper_bottom_to_top(keypoints), np.array([0.0, 0.0, 1.0]))


def stage2_constraint1(keypoints):
    target = keypoints[HAMMER_GRASP] + np.array([0.0, 0.0, GRASP_HEIGHT])
    return _pos_cost(keypoints[EE], target)


def stage2_constraint2(keypoints):
    return _orthogonal_cost(_gripper_left_to_right(keypoints), _hammer_shaft_axis(keypoints))


def stage2_constraint3(keypoints):
    return _samedir_cost(_gripper_bottom_to_top(keypoints), np.array([0.0, 0.0, 1.0]))


def stage4_constraint1(keypoints):
    return abs(keypoints[HAMMER_GRASP][2] - CLEARANCE_HEIGHT)


def stage5_constraint1(keypoints):
    target = keypoints[BLOCK_TOP] + np.array([0.0, 0.0, PRE_STRIKE_HEIGHT])
    return _pos_cost(keypoints[HAMMER_HEAD], target)


def stage6_constraint1(keypoints):
    return _pos_cost(keypoints[HAMMER_HEAD], keypoints[BLOCK_TOP])
