from __future__ import annotations

import numpy as np

_pos_cost = globals().get("_pos_cost")
_samedir_cost = globals().get("_samedir_cost")
_unit = globals().get("_unit")


# 1 = GRASP, -1 = RELEASE, 0 = MOVE/CONSTRAIN
grasp_stage = [
    0, 0, 1, 0, 0, 0, -1, 0,
    0, 0, 1, 0, 0, 0, -1, 0,
    0, 0, 1, 0, 0, 0, -1,
]
num_stages = len(grasp_stage)
grasp_keypoints = [
    -1, -1, 1, -1, -1, -1, -1, -1,
    -1, -1, 4, -1, -1, -1, -1, -1,
    -1, -1, 7, -1, -1, -1, -1,
]


EE = 0
EE_LEFT = -2
EE_RIGHT = -1

RED_CENTER = 1
GREEN_CENTER = 4
BLUE_CENTER = 7

RED_TARGET_POSITION_XY = np.array([0.25, -0.08])
GREEN_TARGET_POSITION_XY = np.array([0.25, 0.0])
BLUE_TARGET_POSITION_XY = np.array([0.25, 0.08])

APPROACH_HEIGHT = 0.08
GRASP_HEIGHT = 0.005
LIFT_HEIGHT = 0.14
PRE_PLACE_HEIGHT = 0.07
RETREAT_HEIGHT = 0.16


def _gripper_bottom_to_top(keypoints):
    finger_center = (keypoints[EE_LEFT] + keypoints[EE_RIGHT]) / 2.0
    return _unit(finger_center - keypoints[EE])


def _gripper_left_to_right(keypoints):
    return _unit(keypoints[EE_RIGHT] - keypoints[EE_LEFT])


def _approach_cost(keypoints, block_center):
    target = keypoints[block_center] + np.array([0.0, 0.0, APPROACH_HEIGHT])
    return _pos_cost(keypoints[EE], target)


def _grasp_cost(keypoints, block_center):
    target = keypoints[block_center] + np.array([0.0, 0.0, GRASP_HEIGHT])
    return _pos_cost(keypoints[EE], target)


def _top_down_cost(keypoints):
    return _samedir_cost(_gripper_bottom_to_top(keypoints), np.array([0.0, 0.0, 1.0]))


def _fixed_yaw_cost(keypoints):
    return _samedir_cost(_gripper_left_to_right(keypoints), np.array([0.0, -1.0, 0.0]))


def _lift_cost(keypoints, block_center):
    return abs(keypoints[block_center][2] - LIFT_HEIGHT)


def _target_position(keypoints, block_center, target_position_xy):
    block_half_size = abs(keypoints[block_center][2] - keypoints[block_center + 1][2])
    return np.array([target_position_xy[0], target_position_xy[1], block_half_size])


def _pre_place_cost(keypoints, block_center, target_position_xy):
    target_position = _target_position(keypoints, block_center, target_position_xy)
    target_position = target_position + np.array([0.0, 0.0, PRE_PLACE_HEIGHT])
    return _pos_cost(keypoints[block_center], target_position)


def _place_cost(keypoints, block_center, target_position_xy):
    target_position = _target_position(keypoints, block_center, target_position_xy)
    return _pos_cost(keypoints[block_center], target_position)


def _retreat_cost(keypoints):
    return abs(keypoints[EE][2] - RETREAT_HEIGHT)


def stage1_constraint1(keypoints):
    return _approach_cost(keypoints, RED_CENTER)


def stage1_constraint2(keypoints):
    return _top_down_cost(keypoints)


def stage1_constraint3(keypoints):
    return _fixed_yaw_cost(keypoints)


def stage2_constraint1(keypoints):
    return _grasp_cost(keypoints, RED_CENTER)


def stage2_constraint2(keypoints):
    return _top_down_cost(keypoints)


def stage2_constraint3(keypoints):
    return _fixed_yaw_cost(keypoints)


def stage4_constraint1(keypoints):
    return _lift_cost(keypoints, RED_CENTER)


def stage5_constraint1(keypoints):
    return _pre_place_cost(keypoints, RED_CENTER, RED_TARGET_POSITION_XY)


def stage6_constraint1(keypoints):
    return _place_cost(keypoints, RED_CENTER, RED_TARGET_POSITION_XY)


def stage8_constraint1(keypoints):
    return _retreat_cost(keypoints)


def stage9_constraint1(keypoints):
    return _approach_cost(keypoints, GREEN_CENTER)


def stage9_constraint2(keypoints):
    return _top_down_cost(keypoints)


def stage9_constraint3(keypoints):
    return _fixed_yaw_cost(keypoints)


def stage10_constraint1(keypoints):
    return _grasp_cost(keypoints, GREEN_CENTER)


def stage10_constraint2(keypoints):
    return _top_down_cost(keypoints)


def stage10_constraint3(keypoints):
    return _fixed_yaw_cost(keypoints)


def stage12_constraint1(keypoints):
    return _lift_cost(keypoints, GREEN_CENTER)


def stage13_constraint1(keypoints):
    return _pre_place_cost(keypoints, GREEN_CENTER, GREEN_TARGET_POSITION_XY)


def stage14_constraint1(keypoints):
    return _place_cost(keypoints, GREEN_CENTER, GREEN_TARGET_POSITION_XY)


def stage16_constraint1(keypoints):
    return _retreat_cost(keypoints)


def stage17_constraint1(keypoints):
    return _approach_cost(keypoints, BLUE_CENTER)


def stage17_constraint2(keypoints):
    return _top_down_cost(keypoints)


def stage17_constraint3(keypoints):
    return _fixed_yaw_cost(keypoints)


def stage18_constraint1(keypoints):
    return _grasp_cost(keypoints, BLUE_CENTER)


def stage18_constraint2(keypoints):
    return _top_down_cost(keypoints)


def stage18_constraint3(keypoints):
    return _fixed_yaw_cost(keypoints)


def stage20_constraint1(keypoints):
    return _lift_cost(keypoints, BLUE_CENTER)


def stage21_constraint1(keypoints):
    return _pre_place_cost(keypoints, BLUE_CENTER, BLUE_TARGET_POSITION_XY)


def stage22_constraint1(keypoints):
    return _place_cost(keypoints, BLUE_CENTER, BLUE_TARGET_POSITION_XY)
