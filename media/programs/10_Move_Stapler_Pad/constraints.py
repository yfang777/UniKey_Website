from __future__ import annotations

import numpy as np

_pos_cost = globals().get("_pos_cost")
_samedir_cost = globals().get("_samedir_cost")
_unit = globals().get("_unit")


# 1 = GRASP/CLOSE, -1 = RELEASE/OPEN, 0 = MOVE/CONSTRAIN
grasp_stage = [
    0,  # 1. Move to the pre-grasp above the stapler
    0,  # 2. Move to the stapler
    1,  # 3. Grasp the stapler
    0,  # 4. Move above the colored pad
    0,  # 5. Place and align the stapler on the pad
    -1,  # 6. Release the stapler
]
num_stages = len(grasp_stage)
grasp_keypoints = [-1, -1, 1, -1, -1, -1]


EE = 0
STAPLER_GRASP = 1
STAPLER_FORWARD = 2
STAPLER_RIGHT = 3
PAD_TARGET_CENTER = 4
PAD_TARGET_FRONT = 5
EE_LEFT = -2
EE_RIGHT = -1

PRE_GRASP_HEIGHT = 0.08
PRE_PLACE_HEIGHT = 0.10


def _gripper_bottom_to_top(keypoints):
    finger_center = (keypoints[EE_LEFT] + keypoints[EE_RIGHT]) / 2.0
    return _unit(finger_center - keypoints[EE])


def _gripper_left_to_right(keypoints):
    return _unit(keypoints[EE_RIGHT] - keypoints[EE_LEFT])


def _stapler_direction(keypoints):
    return _unit(keypoints[STAPLER_FORWARD] - keypoints[STAPLER_GRASP])


def _stapler_right_direction(keypoints):
    return _unit(keypoints[STAPLER_RIGHT] - keypoints[STAPLER_GRASP])


def _target_direction(keypoints):
    return _unit(keypoints[PAD_TARGET_FRONT] - keypoints[PAD_TARGET_CENTER])


def stage1_constraint1(keypoints):
    target = keypoints[STAPLER_GRASP] + np.array([0.0, 0.0, PRE_GRASP_HEIGHT])
    return _pos_cost(keypoints[EE], target)


def stage1_constraint2(keypoints):
    return _samedir_cost(
        _gripper_left_to_right(keypoints),
        _stapler_right_direction(keypoints),
    )


def stage2_constraint1(keypoints):
    return _pos_cost(keypoints[EE], keypoints[STAPLER_GRASP])


def stage2_constraint2(keypoints):
    return _samedir_cost(
        _gripper_bottom_to_top(keypoints),
        np.array([0.0, 0.0, 1.0]),
    )


def stage4_constraint1(keypoints):
    target = keypoints[PAD_TARGET_CENTER] + np.array([0.0, 0.0, PRE_PLACE_HEIGHT])
    return _pos_cost(keypoints[STAPLER_GRASP], target)


def stage4_constraint2(keypoints):
    return _samedir_cost(_stapler_direction(keypoints), _target_direction(keypoints))


def stage5_constraint1(keypoints):
    return _pos_cost(keypoints[STAPLER_GRASP], keypoints[PAD_TARGET_CENTER] - np.array([0., 0.02, 0.]))


def stage5_constraint2(keypoints):
    return _samedir_cost(_stapler_direction(keypoints), _target_direction(keypoints))
