# UniKey project website

Static project page for **UniKey: Keypoints as a Unified Interface for Scalable Data Generation and Policy Learning**, with author names and affiliations for Columbia University and Toyota Research Institute.

## Preview

Run from this directory:

```sh
python3 scripts/preview.py --port 8000
```

Open http://localhost:8000. The dependency-free preview server supports byte-range requests so video scrubbing works. There is no build step. Asset URLs are relative, so the site can also be hosted under a repository subdirectory. Source Serif 4 is served locally, with Georgia and serif fallbacks. Its SIL Open Font License is included in `assets/fonts/`.

## Deployment

Repository: [yfang777/UniKey_Website](https://github.com/yfang777/UniKey_Website).

The GitHub Pages deployment target is [https://yfang777.github.io/UniKey_Website/](https://yfang777.github.io/UniKey_Website/).

The Paper button opens [UniKey.pdf](https://yfang777.github.io/UniKey_Website/UniKey.pdf), the updated manuscript supplied as `CodeGen_ICRA-2.pdf`.

The composed introduction video is included at [output/social/unikey-introduction.mp4](https://yfang777.github.io/UniKey_Website/output/social/unikey-introduction.mp4). Follow deployment progress in [GitHub Actions](https://github.com/yfang777/UniKey_Website/actions/workflows/deploy-pages.yml).

Enable the repository's **Settings → Pages → Build and deployment → Source → GitHub Actions** once. The `Deploy website to GitHub Pages` workflow then validates and deploys every push to `main`; it can also be run manually from the Actions tab. Deployment status and the published URL appear in the `github-pages` environment.

The workflow runs the interaction and JavaScript checks, then uses `scripts/package_site.py` to build `_site/` and verify local HTML and stylesheet asset paths. The bundle contains `index.html`, `.nojekyll`, `UniKey.pdf`, `assets/`, `data/`, `media/`, and the composed social video and poster from `output/social/`. Original uploads, Python caches, source notes, and composition helper files are excluded from the deployed bundle. The repository remains available for development documentation and source scripts.

To inspect the deployment bundle locally:

```sh
python3 scripts/package_site.py
python3 -m http.server 8002 --directory _site
```

The existing `main` history is retained. Push the complete website, including its media assets and deployment workflow, with `git push -u origin main`.

## Page and interactions

The visual design follows the ENPIRE project page, with the five-section reading order agreed in `structure.md`:

1. Introducing UniKey: motivation, the shared keypoint interface, and links to the three capabilities.
2. Expert Data Generation: agentic keypoint programs and four task demonstrations.
3. Automated Detection and Correction of Failure: four task videos and corrective data across rounds.
4. Sim-to-Real: domain-randomization demonstrations followed by real-world executions.
5. Technical Details: Policy Failure Detection and Correction, and Data Efficiency and Robustness.

A full-screen autoplaying video with top-centered phase captions leads into a cream article canvas with Source Serif 4 typography. Text, figures, and demonstrations share an article column up to 965 pixels wide. A sticky outline lists the title, five sections, and technical subsections. At 820 pixels or less, the video fits the screen without cropping and a floating Contents button opens a modal drawer with keyboard focus management, Escape, backdrop, and link dismissal. Existing `#pipeline`, `#evaluation`, `#sim-to-real-results`, `#robotwin`, and individual RoboTwin task links remain available. The old interactive Method and Interactive Corrective Motion Planning demo sources remain archived; the static method figure appears under Technical Details.

The page uses the reference cream (`#f6f6ef`) and near-black (`#0c0c0c`) palette, thin neutral borders, and outlined controls. Task selections use a subtle neutral fill and dark underline.

Article videos automatically play muted and inline when at least half of the player enters view. They pause below 15% visibility or when the browser tab is hidden, and resume from the same position on return. Manual pauses remain paused until the reader presses Play or switches away and back to that task. Selecting another visible task starts its clip from the beginning; hidden task panels never autoplay. Playback speeds are preserved. Finished clips stay at the end. Reduced-motion preferences disable scroll-triggered playback while keeping explicit Play available.

Expert Data Generation has four task-selection buttons: Hang Mug, Arrange Table, Flip and Arrange Shoe, and Pack Battery. Only one task video is visible, defaulting to Hang Mug. Selecting another task switches the video in place without scrolling or changing the URL, highlights the button, pauses the previous video, and resets the selected clip. Arrow Left/Right and Home/End also navigate the buttons. Without JavaScript, the default Hang Mug clip remains available.

The Hang Mug pipeline clip retains all 245 frames of the original v5 live text generation and the 0.5-second shrink into the top-left grid cell. It then plays the selected Blender grid: the original reference, original episodes 02, 03, 10, 12, 18, and 20, and switched episodes 01, 02, 03, 05, and 06. Original 27 is excluded. The grid carries “Generate expert data for different object  initializations” at the top center, using the teaser's exact caption helper: DejaVu Sans Book at 54 pixels in its translucent rounded panel. The combined video is 1920 × 1080 at 30 fps, with 497 frames and a 16.567-second duration. Its original text-generation frames retain identical decoded pixels. Render provenance is saved beside the video in `assets/videos/pipeline/hang-mug/render-info.json`. Rebuild from the sibling visualization repository with `python -m render.publish_hang_mug_expert_grid` using the `codegen_realworld` environment.

Arrange Table, Flip and Arrange Shoe, and Pack Battery use the validated exports under `../Codegen_Blender_Visualization/data/live_text_generation/{task}_grid/{task}_v5_shrink_into_grid_4x3.mp4`. Each retains its full v5 live text generation, removes the text immediately, and shrinks the completed robot scene into the top-left cell of a 4-column by 3-row grid over 0.5 seconds. The same episode then replays from the beginning alongside eleven other episodes; shorter episodes hold their final poses until all finish. The shoe grid contains six forward-X and six forward-Y placements. These clips are 1920 × 1080 at 30 fps, with durations of approximately 41.533, 29.8, and 14.633 seconds, respectively. All four players use the full article width and scale down on smaller screens. Posters show the first frame, and media URLs use content hashes to refresh cached assets.

Automated Detection and Correction of Failure has four task videos selected by its own four-button picker: Hang Mug, Arrange Table, Flip and Arrange Shoe, and Pack Battery. Hang Mug is selected by default. Each task has one full-width video with playback controls and a first-frame poster. The paired players and their “Policy Rollout” and “Correction” labels are removed. Selecting a different task pauses the outgoing video and resets the incoming video. Clicking the active task preserves playback. The picker supports Arrow Left/Right and Home/End and operates independently of the other task selectors. Without JavaScript, the default Hang Mug video remains available with native controls.

Arrange Table uses the validated lossless composition behind `policy_with_divergence_v9.mp4` from `../Codegen_Blender_Visualization/data/automatic_detection_correction/table_arrange_v9/`. Pack Battery uses the first-threshold composition in `pack_battery_v8/`; Flip and Arrange Shoe uses `flip_then_arrange_shoe_v7/`. Hang Mug retains an exact copy of `hang_mug_v7/policy_with_divergence_v7.mp4`. These edits retain the v5 Hang Mug/Pack Battery motion and the v6 Arrange Table/Shoe motion. The latter raises the recorded policy's spoon approach by 8 mm and shoe approach by 20 mm, aligns table-contact envelopes with the visual meshes, and regenerates corrections from exact new rollout states. These are controlled command variations, not fresh learned-policy inference. Physics audits throughout motion and settling, plus checks of every delivered Blender frame, confirm positive tabletop clearance. Both corrections pass task geometry and physical placement checks.

Arrange Table shows the first tolerance crossing (value 2.002125 cm; threshold 2 cm) at 1.366667 seconds, then immediately rewinds from that pose at 1.4 seconds. Pack Battery first exceeds 2 cm at 3.8 seconds (zero-based frame 114, value 2.004707 cm). It displays that pose once, then immediately rewinds from the same pose and chart values at 3.833333 seconds, replacing the former 7.166667-second rewind start. Both tasks omit the former failure pause and all later policy motion. Flip and Arrange Shoe's forward segment still ends at 2.3 seconds of displayed video, including its failure pause. Rewind returns to each existing correction checkpoint. All four rewinds reuse the teaser's cinematic motion trails, cool tint, and animated double-chevron badge; the badge fits the chart title area while the chart remains sharp. Arrange Table switches to 2x its previous video speed after the spoon grasp, at 6.0 seconds, and displays “2x speed” in the upper-right corner of the scene until the end. Motion, keypoints, and chart values accelerate together; the policy, rewind, and grasp retain their timing. All task clips remain 30 fps.

The four clips retain their illustrative divergence visualizations and 30 fps timing. Hang Mug remains 1920 × 1080. Arrange Table, Flip and Arrange Shoe, and Pack Battery are 1904 × 1080: a 16-pixel crop removes their baked-in 15-pixel left gutter and one image column to keep H.264 dimensions even. The scene is not stretched, and the complete divergence chart is retained. Their players and first-frame posters use the cropped native aspect ratio, so the image meets the border without letterboxing. The active divergence bar reaches 1.90 cm after rewind, just below the 2 cm threshold, and correction continues from the same value. These bars remain illustrative rather than measured policy/planner divergence. Durations are approximately 12.133, 13.800, 17.833, and 10.200 seconds for Hang Mug, Arrange Table, Flip and Arrange Shoe, and Pack Battery, respectively. Hang Mug is aligned flush left and ends after the completed release, with the trailing idle frames removed. The videos scale to the article width on desktop and smaller screens without further cropping. Video and poster URLs use refreshed content hashes.

Rebuild these three clips with `python scripts/update_correction_videos.py` in the visualization project's `codegen_realworld` environment. The script accepts `--source-root` and `--task` overrides, creates Pack Battery's first-threshold export with the existing compositor when needed, and encodes directly from the validated lossless frames. It checks every decoded frame, chart region, left edge, timestamp, rewind state, and Pack Battery correction handoff before replacing website assets. `data/correction-videos.json` records source and output hashes, frame counts, crop dimensions, threshold timing, and validation results. Backups, decoded previews, and sequence links stay in `output/correction-videos/`, outside the deployment bundle.

The section ends with an independent four-task picker for policy improvement videos, preceded by a paragraph explaining batched policy rollout, corrective data generation, and policy finetuning on the aggregated dataset. Hang Mug is selected by default. Each task has playback controls and a first-frame poster. Switching tasks pauses the outgoing video and resets the selected clip; clicking the active task preserves playback. Arrow Left/Right and Home/End navigate the buttons without scrolling or changing the URL. Buttons use four columns on desktop and two on mobile. Without JavaScript, the default Hang Mug clip retains native controls and its SVG chart displays the complete available results.

Hang Mug uses the current RoboTwin layout: a native 1440 × 1080 (4:3) correction video on the left and an equal-width SVG chart on the right. The plotting area aligns with the video's top and bottom edges. A square chart canvas reserves room below the axes for dataset-step labels and the evaluation note, with its 4.5% top margin offset in CSS. The panels stack below 580 pixels. The video is re-rendered from the four archived Blender scenes, preserving the original 4:3 camera framing, every frame, moving-camera pose, ghost pose, keypoint overlay, round caption, and the 320-frame / 30 fps / 10.667-second timeline. The footage is neither cropped nor upscaled. The chart matches the current RoboTwin figures: green UniKey and brown Dense Sampling, equal 3.2-point solid lines, smaller checkpoints with thin white outlines, pale 95% exact bootstrap distributions, regular-weight direct labels, and a borderless gold star at the best UniKey checkpoint. The axes use Dataset Steps, as in RoboTwin; round 1 starts at 10k and each subsequent round adds 1k. Each new group of checkpoints draws over 0.9 seconds when its correction clip starts. Drawing follows the media clock, including pauses, backwards seeks, replay, and task changes. Reduced motion and unavailable video show the full static results.

`data/hang-mug-improvement.json` records verified evaluation counts, source hashes, dataset budgets, and the four playback stages. The available UniKey export includes all 19 rounds; the currently available matching Dense Sampling evaluation contains only the shared initial checkpoint. Later Dense Sampling checkpoints must come from the matching 10k-start ACT experiment; the older paper CSV has an 18% initial rate and is not interchangeable with this video's 28% initial evaluation. No missing Dense Sampling rates are invented. Regenerate the inline chart and cache versions with `python3 scripts/update_hang_mug_chart.py`. Re-render the 4:3 video with `python3 scripts/render_hang_mug_rounds.py`, or use `--preview` for representative frames without replacing website assets. Intermediates remain in the sibling artifacts directory; the published video, poster, and render provenance are under `assets/videos/pipeline/failure-detection-correction/hang-mug/training-rounds*`.

The other three policy improvement clips remain exact copies of `../Codegen_Blender_Visualization/data/automatic_detection_correction/{task}_iterations_v2/fast_camera_transition_with_success_rate_v3.mp4`. They are native 1920 × 1080 at 30 fps and use the full article width: Arrange Table lasts 10.4 seconds, Flip and Arrange Shoe 11.333 seconds, and Pack Battery 10.333 seconds. They retain the moving camera, ghost poses, keypoint overlays, and measured success-rate charts. Video, poster, script, and stylesheet URLs use content hashes to refresh cached assets.

Pack Battery shows training rounds 2, 6, 11, and 16 with success rates of 31%, 81%, 93%, and 96%. Flip and Arrange Shoe shows rounds 2, 11, 21, and 31 with success rates of 29%, 59%, 65%, and 72%. Arrange Table shows the two verified checkpoints: the base policy at 86% and the final checkpoint at fine-tuning step 50,000 at 95%. Its chart uses fine-tuning steps rather than aggregation rounds. The original four-round table archive was unavailable, and new intermediate evaluations failed a reproduction control, so those evaluations are excluded. Table corrections were newly simulated from the archived failure states and passed the task constraints; the two displayed evaluation rates were checked against all 200 archived episode outcomes.

Domain Randomization appears within Sim-to-Real, before the real-world rollouts. Its introduction explains randomizing lighting, object textures, backgrounds, and cameras, then finetuning and deploying zero-shot. Prose uses selective bold emphasis without repeated underlining. It has its own four-task selector: Hang Mug, Arrange Table, Flip and Arrange Shoe, and Pack Battery. Buttons use four columns on wide screens and two in narrow layouts. Hang Mug is selected by default, with exactly one video visible. Selecting another task highlights its button, pauses the previous clip, and resets the selected clip without scrolling or changing the URL. Clicking the current task preserves playback. Arrow Left/Right and Home/End navigate the buttons, with accessible selection states and announcements. This selector operates independently of Agentic Keypoint Programs and RoboTwin. Without JavaScript, the default Hang Mug clip remains available.

All four domain-randomization videos include a synchronized 432 × 243 wrist-camera inset at the top left, with a 12-pixel margin, 2-pixel border, and “wrist camera” centered at the top of the inset. The published videos and first-frame posters are copied from the wrist-camera versions in `output/previews/domain-randomization/` (the Hang Mug poster is published as `poster.jpg`). They have playback controls, are centered at up to their native 960-pixel width, and scale to smaller screens while preserving their 960 × 720 resolution, 4:3 aspect ratio, and 50 fps timing. Hang Mug retains its 5.12-second, 256-frame timeline; the other three clips each retain 5 seconds and 250 frames. Video and poster URLs use refreshed content hashes.

The main footage comes from `../Codegen_Blender_Visualization_artifacts/20261008T164407Z/data/visualization/hang_mug/sample_12/planner_d/camera_perspective_1/domain_randomization_camera_4x3/domain_randomization.mp4` for Hang Mug and `../Codegen_Blender_Visualization/data/domain_randomization/{table_arrange,flip_then_arrange_shoe,pack_battery}/domain_randomization_mujoco.mp4` for the other tasks. Rebuild with `python scripts/preview_domain_randomization.py` using the sibling visualization project's Python environment, Blender, and FFmpeg; the archived animation and domain settings in `../Codegen_Blender_Visualization_artifacts/` are required. The script reads these original videos directly, rather than the published wrist-view videos, so rebuilds do not composite the inset twice. The wrist views use the calibrated D405 camera, original geometry animation, and matching per-frame randomization settings, with the same reduced render samples as the local preview. `--skip-render` recomposes the videos from cached wrist frames after layout changes. `--page-only` refreshes `preview-domain-randomization.html#domain-randomization` after website edits without rendering again. The preview page and `output/previews/` media remain excluded from the GitHub Pages deployment bundle; the published copies under `assets/videos/pipeline/domain-randomization/` are included.

Sim-to-Real Results appears under Technical Details → Data Efficiency and Robustness, before Robotwin Benchmark. It displays the previous main-results figure from `media/figures/main-results.png`, scaled to the available width with its original aspect ratio. Both the figure and the visible “View PDF” link open the original full-resolution `media/figures/main-results.pdf` in a new tab.

Robotwin Benchmark is a sibling subsection of Data Efficiency and Robustness under Technical Details, with matching heading typography, spacing, and navigation level. It begins with a brief comparison of UniKey and dense sampling on 10 RoboTwin 2.0 tasks. It uses the shared paragraph typography. The ten RoboTwin task buttons form a grid: five columns on wide screens, three in intermediate layouts, and two at 580 pixels or less. Clicking a task immediately shows its matching keypoint video and success-rate curve in the same location. The selected button is highlighted. Repeated task headings, standalone success-rate summaries, the comparison table, and carousel controls are removed.

Only the selected task panel is visible with JavaScript enabled. Switching tasks pauses the previous clip and resets the newly selected clip. Clicking the current task preserves playback. Arrow Left/Right and Home/End navigate tasks when the task picker or visualization region is focused; video progress sliders retain their own keyboard behavior. Task URL fragments support direct links and browser history. Videos pause when they leave view or the page is hidden. Without JavaScript, all video-and-curve panels remain available vertically.

All ten RoboTwin videos use Blender Cycles and retain their original 1440 × 1080 resolution, 50 fps, camera views, keypoint diamonds, and dashed connections. The stage captions are removed from both clips and posters. No text-generation animation is included. Each plotting area matches its video's height and aligns with its top and bottom edges. The square figure canvases reserve space below the plots for axis labels and evaluation notes; the columns remain equal in width, with playback controls below the videos.

## Editing

- `index.html`: the five blog sections, capability links, technical explanations, real-world rollouts, task demonstrations, and results.
- `assets/site.css`: the ENPIRE-style video opening, serif article, responsive outline, drawer, controls, and media layouts.
- `assets/video-controls.js`: progressive enhancement of all 30 article videos with compact play/pause, progress, video length, and fullscreen controls. Native controls remain the no-JavaScript fallback. Only real-world rollouts have a speed control, defaulting to 30× and cycling through 60× and 100×; other videos play at their original speed without a speed button. The duration to the right of each timeline adjusts to the selected speed.
- `assets/presentation.js`: opening-video playback and reduced-motion behavior, plus the mobile contents dialog.
- `assets/fonts/`: local Source Serif 4 and its font license.
- `assets/videos/hero/`: the supplied opening video and a first-frame poster.
- `assets/site.js`: task selection, keyboard navigation, history, section navigation, and reading progress.
- `assets/video-autoplay.js`: visibility-based article playback, manual pause preservation, background pausing, selected-task playback, and reduced-motion behavior.
- `assets/pipeline.js`: independent Agentic Keypoint Programs, Policy Failure Detection and Correction, Policy Improvement, and Domain Randomization task selection without scrolling, selected-button state, playback reset/pausing, and keyboard navigation.
- `assets/round-improvement.js`: media-synchronized SVG chart drawing for Hang Mug, including pause, seek, replay, and reduced-motion handling.
- `scripts/render_hang_mug_rounds.py`, `scripts/update_hang_mug_chart.py`, and `data/hang-mug-improvement.json`: reproduce the 4:3 correction clip and live chart from archived scenes and verified evaluations.
- `assets/videos/pipeline/`: four full-HD v5 live text → shrink → 4×3 replay-grid clips, served as `combined.mp4`, and their first-frame posters, in `hang-mug/`, `arrange-table/`, `flip-and-arrange-shoe/`, and `pack-battery/`.
- `assets/videos/pipeline/failure-detection-correction/`: cinematic-rewind task clips (v9 Arrange Table, v8 Pack Battery, and v7 Hang Mug/Shoe), served as `{task}/rollout.mp4`, with `{task}/poster.jpg`, plus four policy improvement videos at `{task}/training-rounds.mp4` and `{task}/training-rounds-poster.jpg`. Hang Mug uses the new native 4:3 render. The older paired clips and baked-in Hang Mug chart are no longer referenced by the page.
- `scripts/update_correction_videos.py` and `data/correction-videos.json`: reproduce and validate the three correction clips with their outer left gutter removed, including Pack Battery's immediate threshold-triggered rewind.
- `assets/videos/pipeline/domain-randomization/`: four domain-randomization clips and their first-frame posters.
- `media/robotwin/`: caption-free Blender Cycles demonstrations, posters at 0.5 seconds, SVG success-rate curves, and PNG exports. Each task includes `render-info.json` with render provenance and camera-projection validation.
- `media/figures/main-results.png` and `media/figures/main-results.pdf`: the previous main-results preview and full-resolution PDF, displayed under Sim-to-Real Results.
- `data/visualization-media.json`: dimensions, frame counts, timing, media checksums, and clean-render source checksums for all ten videos.
- `data/robotwin-results.json`: original evaluation counts and archive-relative source paths, plus the source archive SHA-256.
- `scripts/preview.py`: local static preview with byte-range support for video seeking.
- `scripts/update_robotwin.py`: regenerates the curves using task-button labels; it does not recreate a table or result summaries.
- `scripts/update_robotwin_media.py`: recreates keypoint annotations from clean rendered videos and recorded pixel coordinates, omitting stage captions, then refreshes posters, media checksums, and URL cache versions.
- `assets/videos/realworld/`: the four supplied real-world rollouts, with playback controls and `preload="none"`, shown in two columns on desktop and one on mobile.
- `UniKey.pdf`: the updated manuscript supplied as `CodeGen_ICRA-2.pdf`, linked from the Paper button and included in the GitHub Pages bundle.

The current real-world source clips are `/home/yuan/Desktop/{hang_mug,arrange_table,flip_then_arrange_shoe,pack_battery}_w_text.mp4`, including their supplied text overlays. Their web copies are 1920 × 1080 H.264 at 30 fps with original AAC audio, approximately one minute long. They preserve all source frames and timing without trimming, padding, or a final-frame hold. The videos appear under Sim-to-Real → Real-World Execution. The text retains the reported 100% success rate for 30 minutes without real-world demonstrations or policy finetuning.

These clips already encode 30× speed. Their `data-base-speed="30"` attribute makes the controls display 30×, 60×, and 100× while applying file playback rates of 1, 2, and 100/30. The video length at the right end of the timeline updates to approximately 60s, 30s, or 18s. A `data-duration` hint supplies the initial length while `preload="none"` keeps the video deferred; loaded metadata provides the measured duration thereafter. Seeking always uses the original media timeline, so changing speed preserves the current position. Other article videos play at their original speed without a speed control. The older uploads remain locally in ignored `assets/videos/realworld/sources/`.

## Opening video

The opening uses an exact copy of `/home/yuan/codegen/Codegen_Blender_Visualization/data/automatic_detection_correction/hang_mug_teaser_rewind_v3/teaser_rewind_cinematic.mp4`, served as `assets/videos/hero/policy-then-correction.mp4`. It retains the original 1920 × 1080 resolution, 30 fps, 427 frames (about 14.23 seconds), H.264 encoding, and timing. The revised near-rim grasp and controlled variation of recorded policy commands lead into cinematic rewind trails and a regenerated correction. Stage-relevant keypoints remain visible, with connecting lines appearing only during correction. The clip supplies the top-centered phase captions; the page adds no central UNIKEY wordmark. The poster is decoded from its first frame, and video, poster, and stylesheet URLs use content hashes to refresh cached assets. The video loops muted and inline at its original playback rate. A pause/play control remains available; playback pauses when offscreen or the document is hidden, resumes when visible unless manually paused, and respects reduced-motion preferences. No-JavaScript playback retains native video controls and the poster; the desktop article outline and links remain native HTML.

## Results and figures

The RoboTwin results use the supplied `robotwin-results.tar.gz` evaluation export, with experiment variants matched to the original website plots. The Hammer and Bin Dumping figures end at 11k and 5k dataset steps, respectively, where Dense Sampling first reaches 100%; all checkpoints remain in `data/robotwin-results.json`. Other figures show every available checkpoint from their selected runs. The shared initial evaluation follows the original curves and the v19 initialization code, which copies the dense dataset and checkpoint; the export does not include model checkpoints for an independent identity check.

Three tasks differ from the supplied manuscript's Table I: Rank Blocks by Color is 100% / 60% (UniKey / Dense Sampling) at 24k; Rank Blocks by Size is 100% / 93% at 23k; Move Playing Card Away is 100% / 77% at 9k. Move Stapler to Pad remains 91% / 39% at 28k. The 2.65× efficiency metric remains the manuscript's Section IV-B metric, separate from these per-task results.

All ten RoboTwin figures use solid curves with the same 3.2-point line width and 6.5-point checkpoint size for UniKey and Dense Sampling. Both use thin, 0.6-point white checkpoint borders and direct labels in normal font weight. UniKey is green (`#37895b`), and Dense Sampling is deep brown (`#6b4935`). Yellow stars without outlines mark each method's first checkpoint with 100% success; a method that never reaches 100% has no star. Dense Sampling has stars at 11k for Beat Block with Hammer and 5k for Dump Bin into Big Bin. Neither method has a star for Move Stapler to Pad. Pale violin shapes show the central 95% of the exact nonparametric bootstrap distribution of each binary rollout mean: `Binomial(n, successes / n) / n`, with `n = 100`. This describes evaluation sampling uncertainty, not variation across training seeds. At 0% or 100%, the distribution is degenerate, so no violin is drawn. The statistical method is stated on each figure and in its metadata.

Regenerate the curves with Python, matplotlib, numpy, and scipy:

```sh
python3 scripts/update_robotwin.py
```

Regenerate only one task by its website ID:

```sh
python3 scripts/update_robotwin.py --task adjust-bottle
```

Render all ten tasks using their recorded motions, saved presentation cameras, and Blender Cycles on the GPU, then import the caption-free videos and provenance:

```sh
/home/yuan/miniconda3/envs/codegen_realworld/bin/python scripts/render_robotwin_blender.py --resume --jobs 2
/home/yuan/miniconda3/envs/codegen_realworld/bin/python scripts/update_robotwin_media.py
```

The renderer retains every native-rate frame, uses 32 samples with OptiX denoising, and validates every saved keypoint projection against the Blender camera before rendering. The hammer task uses its newer 20261004 recording; the other tasks use the archived 20260922 recordings. `--preview` renders four representative frames per task, and `--task 01_adjust_bottle_01` selects one task. `--resume` retains completed clips whose dimensions, frame count, frame rate, and sample count match the requested settings. Intermediates remain in `../Codegen_Blender_Visualization_artifacts/robotwin_blender_20261028`; `--recording` (with a single task), `--source`, `--visualization`, and `--work-dir` select alternate local inputs and destinations. Use a fresh work directory after changing render settings, because completed PNGs are reused.

The media updater defaults to the completed Blender renders in `../Codegen_Blender_Visualization_artifacts/robotwin_blender_20261028`. Override it with `--source /absolute/path/to/renders`, or use `--task 01_adjust_bottle_01` to update one task. Each task needs `episode_000/clean.mp4`, `coordinates.json`, `style.yaml`, and `render_info.json`. The script checks source and output dimensions, frame counts, frame rates, and durations. It uses saved coordinates without running simulation or changing execution speed, then refreshes posters, provenance, checksums, and media URL cache versions.

## Checks

Run the dependency-free interaction checks and syntax validation:

```sh
node tests/task-picker.cjs
node tests/round-improvement.cjs
node --check assets/site.js
node --check assets/pipeline.js
node --check assets/presentation.js
node --check assets/video-controls.js
node --check assets/video-autoplay.js
node --check assets/round-improvement.js
python3 -m py_compile scripts/update_robotwin.py scripts/update_robotwin_media.py scripts/render_robotwin_blender.py
python3 -m py_compile scripts/render_hang_mug_rounds.py scripts/update_hang_mug_chart.py
```

The task-picker test checks the five-section reading order, navigation targets, and technical headings, then exercises both production handlers with a DOM fixture: independent four-task Agentic Keypoint Programs, Policy Failure Detection and Correction, Policy Improvement, and Domain Randomization selectors, Hang Mug defaults, exactly one visible task block per selector, one video per corrective task with matching media and no paired-player captions, policy improvement media and native dimensions, no selection-induced scrolling or navigation, independent RoboTwin selection, matching media paths and domain media files, selected-button state, playback pausing/reset, keyboard behavior, RoboTwin URL fragments/history, offscreen/background pausing, and the removed sections/table/summaries. It does not verify browser layout or decoding. The older `tests/method-demo.py` targets the archived Method demo and is no longer a check for the current page.
