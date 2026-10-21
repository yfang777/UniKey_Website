# UniKey: Twitter Thread

Each text block contains one numbered post. All six drafts are under 280 characters, including the post number. Video notes and source files follow the post text.

## Post 1: Introduction

```text
1/6 Corrective data is crucial for robust manipulation, but expensive to collect. Could we automate it?

Introducing UniKey: Keypoints as a Unified Interface for Scalable Data Generation and Policy Learning.

Automatic demonstrations + DAgger-style correction.
```

## Post 2: Scalable Data Generation

```text
2/6 Scalable data generation

A VLM agent designs keypoints and writes programs from task descriptions and robot/object geometry.

Iterate on the programs → generate demonstrations across object initializations → train an imitation learning policy.
```

## Post 3: Automatic Corrective Data Generation

```text
3/6 Robust imitation learning takes repeated evaluation and corrective data collection.

UniKey automates the loop:
Evaluate → detect divergence → generate expert corrections → aggregate data → fine-tune → repeat.

Keypoint programs guide detection and correction.
```

## Post 4: Domain Randomization

```text
4/6 From simulation to the real world.

We randomize lighting, textures, backgrounds, and cameras, then fine-tune the policy on the augmented simulation data.

Deploy zero-shot, without real-world demonstrations or real-world policy fine-tuning.
```

## Post 5: Real-World Rollout

```text
5/6 Trained entirely in simulation, UniKey achieves 100% success over 30-minute real-world evaluations.

Tasks: mug hanging, table arrangement, shoe flipping and arrangement, and battery packing.

No real-world demonstrations or real-world policy fine-tuning.
```

## Post 6: Website

```text
6/6 Check out the UniKey website for our paper, code, and videos of scalable data generation, automatic correction, and real-world rollouts.

Columbia University + Toyota Research Institute

https://yfang777.github.io/UniKey_Website/
```

## Video Attachments

| Post | Recommended attachment |
| --- | --- |
| 1 | [Composed introduction video](output/social/unikey-introduction.mp4): approximately 26 seconds, 1920 × 1080, 30 fps. Includes Data Generation → Corrective Data Generation → Domain Randomization → Real-World Rollout, followed by a UniKey end card. Sources: V1, V2, V4, V5. |
| 2 | V1: full program-to-grid video, 15.33 seconds. |
| 3 | V2: failure detection, rewind, and correction. V3 can be appended to show improvement across training rounds. |
| 4 | V4: domain randomization, 5 seconds. |
| 5 | V7: the full real-world shoe rollout. V5–V8 provide all four tasks for an optional montage. Sources already encode 30× playback. |
| 6 | A closing frame or end card with the public project website URL. |

The composed introduction preserves the source playback timing, retains the real-world success counter, and labels that footage as a 30× excerpt from the 30-minute evaluation. It uses Source Serif 4, the website's cream background, short chapter captions, and a silent audio track.

[Introduction edit manifest](output/social/unikey-introduction-edit.json) · [Composition script](output/social/compose_intro.py)

## Video Sources

These links point to the original local source files. Durations and resolutions were checked on 2026-10-21.

| ID | Source file | Duration | Resolution |
| --- | --- | ---: | --- |
| V1 | [Hang Mug: live keypoint program → demonstration grid](/home/yuan/codegen/Codegen_Blender_Visualization/data/live_text_generation/hang_mug_grid/hang_mug_v5_shrink_into_grid_4x3.mp4) | 15.33 s | 1920 × 1080 |
| V2 | [Hang Mug: divergence detection and correction](/home/yuan/codegen/Codegen_Blender_Visualization/data/automatic_detection_correction/hang_mug_v5/policy_with_divergence_v4_3.mp4) | 12.13 s | 1920 × 1080 |
| V3 | [Hang Mug: corrections and success rate across rounds](/home/yuan/codegen/Codegen_Blender_Visualization/data/automatic_detection_correction/hang_mug_iterations_v2/fast_camera_transition_with_success_rate_v3.mp4) | 10.67 s | 800 × 360 |
| V4 | [Hang Mug: domain randomization](/home/yuan/codegen/Codegen_Blender_Visualization/data/domain_randomization/hang_mug/domain_randomization_mujoco.mp4) | 5.00 s | 960 × 720 |
| V5 | [Hang Mug: real-world rollout](/home/yuan/Desktop/hang_mug_w_text.mp4) | 59.93 s | 2560 × 1440 |
| V6 | [Arrange Table: real-world rollout](/home/yuan/Desktop/arrange_table_w_text.mp4) | 59.60 s | 2560 × 1440 |
| V7 | [Flip and Arrange Shoe: real-world rollout](/home/yuan/Desktop/flip_then_arrange_shoe_w_text.mp4) | 59.83 s | 2560 × 1440 |
| V8 | [Pack Battery: real-world rollout](/home/yuan/Desktop/pack_battery_w_text.mp4) | 60.00 s | 2560 × 1440 |

## Editing Notes

- Post 6 includes the public project URL: https://yfang777.github.io/UniKey_Website/.
- The V2+V3 combination, four-task rollout montage, and website end card are optional follow-on edits.
- The copy uses “30 minutes” to match the evaluation reported on the website. The training claim refers to using no real-world demonstrations or real-world policy fine-tuning.
