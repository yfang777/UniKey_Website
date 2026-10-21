# UniKey project website

Static, anonymous project page for **UniKey: Keypoints as a Unified Interface for Scalable Data Generation and Policy Learning**.

## Preview

Run from this directory:

```sh
python3 scripts/preview.py --port 8000
```

Open http://localhost:8000. The dependency-free preview server supports byte-range requests so video scrubbing works. There is no build step. Asset URLs are relative, so the site can also be hosted under a repository subdirectory. Source Serif 4 is served locally, with Georgia and serif fallbacks. Its SIL Open Font License is included in `assets/fonts/`.

## Page and interactions

The visual design follows the ENPIRE project page, with the five-section reading order agreed in `structure.md`:

1. Introducing UniKey: motivation, the shared keypoint interface, and links to the three capabilities.
2. Data Generation: agentic keypoint programs and four task demonstrations.
3. Corrective Data Generation: policy/correction pairs and corrective data across rounds.
4. Sim-to-Real: real-world executions followed by domain-randomization demonstrations.
5. Technical Details: Policy Failure Detection and Correction, Data Efficiency and Robustness, and Scalability.

A full-screen autoplaying video and animated UNIKEY wordmark lead into a cream article canvas with Source Serif 4 typography. Text, figures, and demonstrations share an article column up to 965 pixels wide. A sticky outline lists the title, five sections, and technical subsections. At 820 pixels or less, the video fits the screen without cropping and a floating Contents button opens a modal drawer with keyboard focus management, Escape, backdrop, and link dismissal. Existing `#pipeline`, `#evaluation`, `#sim-to-real-results`, `#robotwin`, and individual RoboTwin task links remain available. The old interactive Method and Interactive Corrective Motion Planning demo sources remain archived; the static method figure appears under Technical Details.

The page uses the reference cream (`#f6f6ef`) and near-black (`#0c0c0c`) palette, thin neutral borders, and outlined controls. Brown and green distinguish policy rollout and correction labels. Task selections use a subtle neutral fill and dark underline.

Data Generation has four task-selection buttons: Hang Mug, Arrange Table, Flip and Arrange Shoe, and Pack Battery. Only one task video is visible, defaulting to Hang Mug. Selecting another task switches the video in place without scrolling or changing the URL, highlights the button, pauses the previous video, and resets the selected clip. Arrow Left/Right and Home/End also navigate the buttons. Without JavaScript, the default Hang Mug clip remains available.

The pipeline clips are exact copies of `combined_horizontal.mp4` from `../Codegen_Blender_Visualization/data/live_text_generation/{hang_mug_v2,arrange_table_v1,flip_and_arrange_shoe_v1,pack_battery_v1}/`. They include the supplied program text and synchronized robot footage, retaining their 1280 × 480 resolution, 30 fps, 8:3 aspect ratio, and original durations. Posters show the first frame.

Corrective Data Generation has four task blocks selected by its own four-button picker: Hang Mug, Arrange Table, Flip and Arrange Shoe, and Pack Battery. Hang Mug is selected by default. Each block shows its own `policy_brown.mp4` on the left, labeled “Policy Rollout”, and `correction_green.mp4` on the right, labeled “Correction”, with independent playback controls and first-frame posters. Selecting a different task pauses both outgoing videos and resets both incoming videos. Clicking the active task preserves playback. The picker supports Arrow Left/Right and Home/End and operates independently of the other task selectors.

All eight clips are exact copies from `../Codegen_Blender_Visualization/data/automatic_detection_correction/`: Hang Mug uses `hang_mug_v2/`, Arrange Table uses `table_arrange_v2/example_2/`, Flip and Arrange Shoe uses `flip_then_arrange_shoe_v2/step_40000_sample_10/`, and Pack Battery uses `pack_battery_v2/`. Desktop columns retain the existing 5:3 width ratio, with policy videos at 1500 × 900 and corrections at 900 × 900; they stack at 580 pixels or less. Original 30 fps timing and each clip's duration are preserved, including the table's 3.4-second policy and the shoe's 5.2-second policy.

The section ends with “Corrective Data Across Rounds”, preceded by a paragraph explaining batched policy rollout, corrective data generation, and policy finetuning on the aggregated dataset. The video is an exact copy of `../Codegen_Blender_Visualization_artifacts/hang_mug_four_rounds_20261011_05x_black_real_rounds/hang_mug_four_rounds_overlay_corrective.mp4`. It has playback controls and a first-frame poster, is centered at up to its native 960-pixel width, and scales to smaller screens while preserving its 960 × 720 resolution, 4:3 aspect ratio, 30 fps timing, and 10.667-second duration.

Domain Randomization appears within Sim-to-Real, after the real-world rollouts. Its introduction explains randomizing lighting, object textures, backgrounds, and cameras, then finetuning and deploying zero-shot. Prose uses selective bold emphasis without repeated underlining. It has its own four-task selector: Hang Mug, Arrange Table, Flip and Arrange Shoe, and Pack Battery. Buttons use four columns on wide screens and two in narrow layouts. Hang Mug is selected by default, with exactly one video visible. Selecting another task highlights its button, pauses the previous clip, and resets the selected clip without scrolling or changing the URL. Clicking the current task preserves playback. Arrow Left/Right and Home/End navigate the buttons, with accessible selection states and announcements. This selector operates independently of Agentic Keypoint Programs and RoboTwin. Without JavaScript, the default Hang Mug clip remains available.

All four domain-randomization videos have playback controls and first-frame posters, are centered at up to their native 960-pixel width, and scale to smaller screens while preserving their 960 × 720 resolution, 4:3 aspect ratio, and 50 fps timing. Hang Mug retains the original 5.12-second clip copied from `../Codegen_Blender_Visualization_artifacts/20261008T164407Z/data/visualization/hang_mug/sample_12/planner_d/camera_perspective_1/domain_randomization_camera_4x3/domain_randomization.mp4`. The other three videos are exact copies of `../Codegen_Blender_Visualization/data/domain_randomization/{table_arrange,flip_then_arrange_shoe,pack_battery}/domain_randomization_mujoco.mp4`, each 5 seconds and 250 frames. Their backgrounds, lighting, textures, camera motion, and timing are preserved.

Sim-to-Real Results appears under Technical Details → Data Efficiency and Robustness, before RoboTwin Results. It displays the previous main-results figure from `media/figures/main-results.png`, scaled to the available width with its original aspect ratio. Both the figure and the visible “View PDF” link open the original full-resolution `media/figures/main-results.pdf` in a new tab.

RoboTwin Results begins with a brief comparison of UniKey and dense sampling on 10 RoboTwin 2.0 tasks. It uses the shared paragraph typography. The ten RoboTwin task buttons form a grid: five columns on wide screens, three in intermediate layouts, and two at 580 pixels or less. Clicking a task immediately shows its matching keypoint video and success-rate curve in the same location. The selected button is highlighted. Repeated task headings, standalone success-rate summaries, the comparison table, and carousel controls are removed.

Only the selected task panel is visible with JavaScript enabled. Switching tasks pauses the previous clip and resets the newly selected clip. Clicking the current task preserves playback. Arrow Left/Right and Home/End navigate tasks when the task picker or visualization region is focused; video progress sliders retain their own keyboard behavior. Task URL fragments support direct links and browser history. Videos pause when they leave view or the page is hidden. Without JavaScript, all video-and-curve panels remain available vertically.

RoboTwin videos retain their original 1440 × 1080 resolution, 50 fps, camera views, keypoint diamonds, and dashed connections. The stage captions are removed from both clips and posters. No text-generation animation is included.

## Editing

- `index.html`: the five blog sections, capability links, technical explanations, real-world rollouts, task demonstrations, and results.
- `assets/site.css`: the ENPIRE-style video opening, serif article, responsive outline, drawer, controls, and media layouts.
- `assets/video-controls.js`: progressive enhancement of all 31 article videos with compact play/pause, speed, progress, and fullscreen controls. Native controls remain the no-JavaScript fallback; playback speed defaults to 1×.
- `assets/presentation.js`: opening-video playback and reduced-motion behavior, plus the mobile contents dialog.
- `assets/fonts/`: local Source Serif 4 and its font license.
- `assets/videos/hero/`: the supplied opening video and a first-frame poster.
- `assets/site.js`: task selection, keyboard navigation, history, offscreen video pausing, section navigation, and reading progress.
- `assets/pipeline.js`: independent Agentic Keypoint Programs, Policy Failure Detection and Correction, and Domain Randomization task selection without scrolling, selected-button state, playback reset/pausing, and keyboard navigation.
- `assets/videos/pipeline/`: four supplied combined clips and their first-frame posters, in `hang-mug/`, `arrange-table/`, `flip-and-arrange-shoe/`, and `pack-battery/`.
- `assets/videos/pipeline/failure-detection-correction/`: four policy/correction pairs and their first-frame posters, plus the Corrective Data Across Rounds clip. Hang Mug retains the original directory; the other pairs use task subdirectories.
- `assets/videos/pipeline/domain-randomization/`: four domain-randomization clips and their first-frame posters.
- `media/robotwin/`: caption-free MuJoCo demonstrations, posters at 0.5 seconds, SVG success-rate curves, and PNG exports.
- `media/figures/main-results.png` and `media/figures/main-results.pdf`: the previous main-results preview and full-resolution PDF, displayed under Sim-to-Real Results.
- `data/visualization-media.json`: dimensions, frame counts, timing, media checksums, and clean-render source checksums for all ten videos.
- `data/robotwin-results.json`: original evaluation counts and archive-relative source paths, plus the source archive SHA-256.
- `scripts/preview.py`: local static preview with byte-range support for video seeking.
- `scripts/update_robotwin.py`: regenerates the curves using task-button labels; it does not recreate a table or result summaries.
- `scripts/update_robotwin_media.py`: recreates keypoint annotations from clean rendered videos and recorded pixel coordinates, omitting stage captions, then refreshes posters, media checksums, and URL cache versions.
- `assets/videos/realworld/`: the four supplied real-world rollouts, with playback controls and `preload="none"`, shown in two columns on desktop and one on mobile.
- `media/paper/unikey.pdf`: the supplied anonymous manuscript (`CodeGen_ICRA.pdf`).

The current real-world source clips, retained locally in ignored `assets/videos/realworld/sources/`, are `Hang_Mug_1Minute_16by9.mp4`, `Table_Arrange_1Minute_16by9.mp4`, `Flip_Shoe_16by9.mp4`, and `Pack_Battery_16by9.mp4`. Their web copies are 1920 × 1080 H.264 at 30 fps with original AAC audio, approximately one minute long. No trimming, speed change, overlays, padding, or final-frame hold is applied. The videos appear under Sim-to-Real → Real-World Execution. The text retains the reported 100% success rate for more than 30 minutes without real-world demonstrations or policy finetuning, and a caption identifies the supplied videos as 30× playback, with approximately one minute of video per task.

## Opening video

The opening uses an exact copy of `/home/yuan/codegen/Codegen_Blender_Visualization/data/automatic_detection_correction/hang_mug_v4/policy_then_correction_v4_8.mp4`, served as `assets/videos/hero/policy-then-correction.mp4`. It retains the original 1920 × 1080 resolution, 30 fps, 14.4-second duration, H.264 encoding, and timing. The poster is its first frame. The video loops muted and inline at its original playback rate. A pause/play control remains available; playback pauses when offscreen or the document is hidden, resumes when visible unless manually paused, and respects reduced-motion preferences. No-JavaScript playback retains native video controls and the poster; the desktop article outline and links remain native HTML.

## Results and figures

The RoboTwin results use the supplied `robotwin-results.tar.gz` evaluation export, with experiment variants matched to the original website plots. Curves retain every available checkpoint from the selected runs. The shared initial evaluation follows the original curves and the v19 initialization code, which copies the dense dataset and checkpoint; the export does not include model checkpoints for an independent identity check.

Three tasks differ from the supplied manuscript's Table I: Rank Blocks by Color is 100% / 60% (UniKey / Dense Sampling) at 24k; Rank Blocks by Size is 100% / 93% at 23k; Move Playing Card Away is 100% / 77% at 9k. Move Stapler to Pad remains 91% / 39% at 28k. The 2.65× efficiency metric remains the manuscript's Section IV-B metric, separate from these per-task results.

Figures use muted green and gray, direct curve labels, and stars at the best UniKey checkpoint and the first perfect Dense Sampling checkpoint when present. Pale violin shapes show the central 95% of the exact nonparametric bootstrap distribution of each binary rollout mean: `Binomial(n, successes / n) / n`, with `n = 100`. This describes evaluation sampling uncertainty, not variation across training seeds. At 0% or 100%, the distribution is degenerate, so no violin is drawn. The statistical method is stated on each figure and in its metadata.

Regenerate the curves with Python, matplotlib, numpy, and scipy:

```sh
python3 scripts/update_robotwin.py
```

Recreate the caption-free videos with the existing Datagen environment, imageio, numpy, Pillow, PyYAML, and FFmpeg:

```sh
/home/yuan/miniconda3/envs/codegen/bin/python scripts/update_robotwin_media.py
```

The default source is `../Codegen_Robotwin_Mujoco/data/visualization`. Override it with `--source /absolute/path/to/visualization`. Each task needs its original `episode_000/clean.mp4`, `coordinates.json`, and `style.yaml`. The script checks source and output dimensions, frame counts, frame rates, and durations. It uses saved coordinates without running simulation or changing execution speed. Use this script after refreshing upstream renders to keep stage captions out of the website videos.

## Checks

Run the dependency-free interaction checks and syntax validation:

```sh
node tests/task-picker.cjs
node --check assets/site.js
node --check assets/pipeline.js
node --check assets/presentation.js
node --check assets/video-controls.js
python3 -m py_compile scripts/update_robotwin.py scripts/update_robotwin_media.py
```

The task-picker test checks the five-section reading order, navigation targets, and technical headings, then exercises both production handlers with a DOM fixture: independent four-task Agentic Keypoint Programs, Policy Failure Detection and Correction, and Domain Randomization selectors, Hang Mug defaults, exactly one visible task block per selector, including both policy/correction players, no selection-induced scrolling or navigation, independent RoboTwin selection, matching media paths and domain media files, selected-button state, playback pausing/reset, keyboard behavior, RoboTwin URL fragments/history, offscreen/background pausing, and the removed sections/table/summaries. It does not verify browser layout or decoding. The older `tests/method-demo.py` targets the archived Method demo and is no longer a check for the current page.
