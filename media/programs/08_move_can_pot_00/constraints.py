from __future__ import annotations

import numpy as np

_pos_cost = globals().get("_pos_cost")
_samedir_cost = globals().get("_samedir_cost")
_unit = globals().get("_unit")


# 1 = GRASP/CLOSE, -1 = RELEASE/OPEN, 0 = MOVE/CONSTRAIN
grasp_stage = [
    0,  # 1. Move to the pre-grasp above the can
    0,  # 2. Move to the can grasp point
    1,  # 3. Grasp the can
    0,  # 4. Move to the pre-place above the pot's left point
    0,  # 5. Move to the pot's left point
    -1,  # 6. Release the can
]
num_stages = len(grasp_stage)
grasp_keypoints = [-1, -1, 3, -1, -1, -1]


EE = 0
POT_CENTER = 1
POT_RIGHT = 2
CAN_GRASP = 3
EE_LEFT = -2
EE_RIGHT = -1

PRE_GRASP_HEIGHT = 0.08
PRE_PLACE_HEIGHT = 0.2
PLACE_DISTANCE = 0.18
PLACE_HEIGHT_OFFSET = 0.003


def _pot_left(keypoints):
    right_direction = _unit(keypoints[POT_RIGHT] - keypoints[POT_CENTER])
    return (
        keypoints[POT_CENTER]
        + PLACE_DISTANCE * right_direction
        + np.array([0.0, 0.0, PLACE_HEIGHT_OFFSET])
    )


def _gripper_bottom_to_top(keypoints):
    finger_center = (keypoints[EE_LEFT] + keypoints[EE_RIGHT]) / 2.0
    return _unit(finger_center - keypoints[EE])


def stage1_constraint1(keypoints):
    target = keypoints[CAN_GRASP] + np.array([0.0, 0.0, PRE_GRASP_HEIGHT])
    return _pos_cost(keypoints[EE], target)


def stage1_constraint2(keypoints):
    return _samedir_cost(
        _gripper_bottom_to_top(keypoints),
        np.array([0.0, 0.0, 1.0]),
    )


def stage2_constraint1(keypoints):
    return _pos_cost(keypoints[EE], keypoints[CAN_GRASP])


def stage2_constraint2(keypoints):
    return _samedir_cost(
        _gripper_bottom_to_top(keypoints),
        np.array([0.0, 0.0, 1.0]),
    )


def stage4_constraint1(keypoints):
    target = _pot_left(keypoints) + np.array([0.0, 0.0, PRE_PLACE_HEIGHT])
    return _pos_cost(keypoints[CAN_GRASP], target)


def stage4_constraint2(keypoints):
    return _samedir_cost(
        _gripper_bottom_to_top(keypoints),
        np.array([0.0, 0.0, 1.0]),
    )


def stage5_constraint1(keypoints):
    return _pos_cost(keypoints[CAN_GRASP], _pot_left(keypoints))


def stage5_constraint2(keypoints):
    return _samedir_cost(
        _gripper_bottom_to_top(keypoints),
        np.array([0.0, 0.0, 1.0]),
    )
