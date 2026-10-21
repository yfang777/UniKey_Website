from __future__ import annotations

import numpy as np

_orthogonal_cost = globals().get("_orthogonal_cost")
_pos_cost = globals().get("_pos_cost")
_samedir_cost = globals().get("_samedir_cost")
_unit = globals().get("_unit")


# 1 = GRASP, -1 = RELEASE, 0 = MOVE/CONSTRAIN
grasp_stage = [
    0,  # 1. Approach the bottle
    0,  # 2. Move to the grasp point
    1,  # 3. Grasp the bottle
    0,  # 4. Lift the bottle clear of the table
    0,  # 5. Hold the bottle at the target pose
    0,
]
num_stages = len(grasp_stage)

grasp_keypoints = [
    -1,
    -1,
    1,
    -1,
    -1,
    -1,
]


EE = 0
EE_LEFT = -2
EE_RIGHT = -1

BOTTLE_GRASP = 1
BOTTLE_UP = 2
BOTTLE_ASIDE = 3

APPROACH_HEIGHT = 0.08
GRASP_HEIGHT = -0.02
CLEARANCE_HEIGHT = 0.15
CLEARANCE_HEIGHT_2 = 0.2


def _bottle_dir(keypoints):
    direction = -(keypoints[BOTTLE_GRASP] - keypoints[BOTTLE_ASIDE])
    direction[2] = 0.0
    return _unit(direction)



def _bottle_axis(keypoints):
    return _unit(keypoints[BOTTLE_UP] - keypoints[BOTTLE_GRASP])


def _bottle_center(keypoints):
    return keypoints[BOTTLE_GRASP]


def _gripper_bottom_to_top(keypoints):
    finger_center = (keypoints[EE_LEFT] + keypoints[EE_RIGHT]) / 2.0
    return _unit(finger_center - keypoints[EE])


def _gripper_left_to_right(keypoints):
    return _unit(keypoints[EE_RIGHT] - keypoints[EE_LEFT])


def stage1_constraint1(keypoints):
    target = keypoints[BOTTLE_GRASP] + np.array([0.0, 0.0, APPROACH_HEIGHT])
    return _pos_cost(keypoints[EE], target)

def stage1_constraint2(keypoints):
    return _samedir_cost(_gripper_left_to_right(keypoints), _bottle_dir(keypoints))


def stage1_constraint3(keypoints):
    return _samedir_cost(_gripper_bottom_to_top(keypoints), np.array([0.0, 0.0, 1.0]))


def stage2_constraint1(keypoints):
    target = keypoints[BOTTLE_GRASP] + np.array([0.0, 0.0, GRASP_HEIGHT])
    return _pos_cost(keypoints[EE], target)


def stage2_constraint2(keypoints):
    return _samedir_cost(_gripper_left_to_right(keypoints), _bottle_dir(keypoints))


def stage2_constraint3(keypoints):
    return _samedir_cost(_gripper_bottom_to_top(keypoints), np.array([0.0, 0.0, 1.0]))


# def stage4_constraint1(keypoints):
#     return abs(_bottle_center(keypoints)[2] - CLEARANCE_HEIGHT)

def stage4_constraint1(keypoints):
    return _pos_cost(_bottle_center(keypoints), np.array([0.35, 0.15, 0.2]))

def stage4_constraint2(keypoints):
    return _samedir_cost(_gripper_left_to_right(keypoints), np.array([0.0, -1.0, 0.0]))

def stage5_constraint1(keypoints):
    return _pos_cost(_bottle_center(keypoints), np.array([0.35, 0.25, 0.4]))

# def stage5_constraint2(keypoints):
#     return _samedir_cost(_bottle_axis(keypoints), np.array([0.0, 0.0, 1.0]))

def stage5_constraint2(keypoints):
    return _samedir_cost(_gripper_left_to_right(keypoints), np.array([0.0, -1.0, 0.0]))

def stage5_constraint3(keypoints):
    return _samedir_cost(_gripper_bottom_to_top(keypoints), np.array([-1.0, 0.0, 0.0]))

def stage6_constraint1(keypoints):
    return _pos_cost(_bottle_center(keypoints), np.array([0.35, 0.25, 0.13]))

def stage6_constraint2(keypoints):
    return _samedir_cost(_gripper_left_to_right(keypoints), np.array([0.0, -1.0, 0.0]))

def stage6_constraint3(keypoints):
    return _samedir_cost(_gripper_bottom_to_top(keypoints), np.array([-1.0, 0.0, 0.0]))


# def stage6_constraint1(keypoints):
#     return _pos_cost(_bottle_center(keypoints), np.array([0.35, -0.2, 0.05]))

# def stage6_constraint2(keypoints):
#     return _samedir_cost(_bottle_axis(keypoints), np.array([0.0, 0.0, 1.0]))

# def stage6_constraint3(keypoints):
#     return _samedir_cost(_gripper_left_to_right(keypoints), np.array([0.0, -1.0, 0.0]))