from __future__ import annotations

import numpy as np

_orthogonal_cost = globals().get("_orthogonal_cost")
_pos_cost = globals().get("_pos_cost")
_samedir_cost = globals().get("_samedir_cost")
_unit = globals().get("_unit")


# 1 = GRASP/CLOSE, -1 = RELEASE/OPEN, 0 = MOVE/CONSTRAIN
grasp_stage = [
    0,  # 1. Move to pre-grasp and orient the gripper
    0,  # 2. Move to grasp
    1,  # 3. Grasp
    0,  # 4. Move to pre-place
    0,  # 5. Place
    -1,  # 6. Release
]
num_stages = len(grasp_stage)
grasp_keypoints = [-1, -1, 1, -1, -1, -1]


EE = 0
CARD_GRASP = 1
CARD_GRASP_FORWARD = 2
EE_LEFT = -2
EE_RIGHT = -1

CARD_GRASP_TARGET = np.array([0.3, 0.07, 0.03])
CARD_FORWARD_TARGET = np.array([0.0, 1.0, 0.0])
PRE_GRASP_HEIGHT = 0.08
PRE_PLACE_HEIGHT = 0.10


def _card_forward(keypoints):
    return _unit(keypoints[CARD_GRASP_FORWARD] - keypoints[CARD_GRASP])


def _gripper_bottom_to_top(keypoints):
    finger_center = (keypoints[EE_LEFT] + keypoints[EE_RIGHT]) / 2.0
    return _unit(finger_center - keypoints[EE])


def _gripper_left_to_right(keypoints):
    return _unit(keypoints[EE_RIGHT] - keypoints[EE_LEFT])


def stage1_constraint1(keypoints):
    target = keypoints[CARD_GRASP] + np.array([0.0, 0.0, PRE_GRASP_HEIGHT])
    return _pos_cost(keypoints[EE], target)


def stage1_constraint2(keypoints):
    return _orthogonal_cost(
        _gripper_left_to_right(keypoints),
        _card_forward(keypoints),
    )


def stage1_constraint3(keypoints):
    return _samedir_cost(
        _gripper_bottom_to_top(keypoints),
        np.array([0.0, 0.0, 1.0]),
    )


def stage2_constraint1(keypoints):
    return _pos_cost(keypoints[EE], keypoints[CARD_GRASP])


def stage2_constraint2(keypoints):
    return _orthogonal_cost(
        _gripper_left_to_right(keypoints),
        _card_forward(keypoints),
    )


def stage2_constraint3(keypoints):
    return _samedir_cost(
        _gripper_bottom_to_top(keypoints),
        np.array([0.0, 0.0, 1.0]),
    )


def stage4_constraint1(keypoints):
    target = CARD_GRASP_TARGET + np.array([0.0, 0.0, PRE_PLACE_HEIGHT])
    return _pos_cost(keypoints[CARD_GRASP], target)


def stage4_constraint2(keypoints):
    return _samedir_cost(_card_forward(keypoints), CARD_FORWARD_TARGET)


def stage5_constraint1(keypoints):
    return _pos_cost(keypoints[CARD_GRASP], CARD_GRASP_TARGET)


def stage5_constraint2(keypoints):
    return _samedir_cost(_card_forward(keypoints), CARD_FORWARD_TARGET)
