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
2. Data Generation: agentic keypoint programs and four task demonstrations.
3. Corrective Data Generation: four task videos and corrective data across rounds.
4. Sim-to-Real: domain-randomization demonstrations followed by real-world executions.
5. Technical Details: Policy Failure Detection and Correction, and Data Efficiency and Robustness.

A full-screen autoplaying video and animated UNIKEY wordmark lead into a cream article canvas with Source Serif 4 typography. Text, figures, and demonstrations share an article column up to 965 pixels wide. A sticky outline lists the title, five sections, and technical subsections. At 820 pixels or less, the video fits the screen without cropping and a floating Contents button opens a modal drawer with keyboard focus management, Escape, backdrop, and link dismissal. Existing `#pipeline`, `#evaluation`, `#sim-to-real-results`, `#robotwin`, and individual RoboTwin task links remain available. The old interactive Method and Interactive Corrective Motion Planning demo sources remain archived; the static method figure appears under Technical Details.

The page uses the reference cream (`#f6f6ef`) and near-black (`#0c0c0c`) palette, thin neutral borders, and outlined controls. Task selections use a subtle neutral fill and dark underline.

Data Generation has four task-selection buttons: Hang Mug, Arrange Table, Flip and Arrange Shoe, and Pack Battery. Only one task video is visible, defaulting to Hang Mug. Selecting another task switches the video in place without scrolling or changing the URL, highlights the button, pauses the previous video, and resets the selected clip. Arrow Left/Right and Home/End also navigate the buttons. Without JavaScript, the default Hang Mug clip remains available.

The pipeline clips are exact copies of the validated exports under `../Codegen_Blender_Visualization/data/live_text_generation/{task}_grid/{task}_v5_shrink_into_grid_4x3.mp4`. Each retains its full v5 live text generation, removes the text immediately, and shrinks the completed robot scene into the top-left cell of a 4-column by 3-row grid over 0.5 seconds. The same episode then replays without text from the beginning alongside eleven other episodes; shorter episodes hold their final poses until all finish. The shoe grid contains six forward-X and six forward-Y placements. All four files are 1920 × 1080 at 30 fps, with a 16:9 aspect ratio. Hang Mug, Arrange Table, Flip and Arrange Shoe, and Pack Battery last approximately 15.333, 41.533, 29.8, and 14.633 seconds, respectively. The player and controls use the full article width and scale down on smaller screens. Posters show the first frame; video, poster, and stylesheet URLs use content hashes to refresh cached assets.

Corrective Data Generation has four task videos selected by its own four-button picker: Hang Mug, Arrange Table, Flip and Arrange Shoe, and Pack Battery. Hang Mug is selected by default. Each task has one full-width video with playback controls and a first-frame poster. The paired players and their “Policy Rollout” and “Correction” labels are removed. Selecting a different task pauses the outgoing video and resets the incoming video. Clicking the active task preserves playback. The picker supports Arrow Left/Right and Home/End and operates independently of the other task selectors. Without JavaScript, the default Hang Mug video remains available with native controls.

All four clips are exact copies of `policy_with_divergence_v4_3.mp4` from `../Codegen_Blender_Visualization/data/automatic_detection_correction/{hang_mug_v5,table_arrange_v5,flip_then_arrange_shoe_v5,pack_battery_v5}/`. They retain their supplied illustrative divergence visualizations, native 1920 × 1080 resolution, 16:9 aspect ratio, and 30 fps timing. The active divergence bar reaches 1.90 cm after rewind, just below the 2 cm threshold, and correction continues from the same value. Durations are approximately 12.133, 25.7, 23.733, and 15.867 seconds, respectively. Hang Mug is aligned flush left and ends after the completed release, with the trailing idle frames removed. The videos scale to the article width on desktop and smaller screens without cropping. Video, poster, and stylesheet URLs use refreshed content hashes.

The section ends with an independent four-task picker for policy improvement videos, preceded by a paragraph explaining batched policy rollout, corrective data generation, and policy finetuning on the aggregated dataset. Hang Mug is selected by default. Each task has playback controls and a first-frame poster. Switching tasks pauses the outgoing video and resets the selected clip; clicking the active task preserves playback. Arrow Left/Right and Home/End navigate the buttons without scrolling or changing the URL. Buttons use four columns on desktop and two on mobile. Videos preserve their native aspect ratios and scale down to the available article width. Without JavaScript, the original Hang Mug video remains available with native controls.

These are exact copies of `../Codegen_Blender_Visualization/data/automatic_detection_correction/{task}_iterations_v2/fast_camera_transition_with_success_rate_v3.mp4`. Hang Mug retains its original 800 × 360 resolution, 20:9 aspect ratio, 30 fps timing, 10.667-second duration, and 800-pixel maximum display width. The three new clips are native 1920 × 1080 at 30 fps and use the full article width: Arrange Table lasts 10.4 seconds, Flip and Arrange Shoe 11.333 seconds, and Pack Battery 10.333 seconds. They retain the moving camera, ghost poses, keypoint overlays, and measured success-rate charts. Video, poster, script, and stylesheet URLs use content hashes to refresh cached assets.

Pack Battery shows training rounds 2, 6, 11, and 16 with success rates of 31%, 81%, 93%, and 96%. Flip and Arrange Shoe shows rounds 2, 11, 21, and 31 with success rates of 29%, 59%, 65%, and 72%. Arrange Table shows the two verified checkpoints: the base policy at 86% and the final checkpoint at fine-tuning step 50,000 at 95%. Its chart uses fine-tuning steps rather than aggregation rounds. The original four-round table archive was unavailable, and new intermediate evaluations failed a reproduction control, so those evaluations are excluded. Table corrections were newly simulated from the archived failure states and passed the task constraints; the two displayed evaluation rates were checked against all 200 archived episode outcomes.

Domain Randomization appears within Sim-to-Real, before the real-world rollouts. Its introduction explains randomizing lighting, object textures, backgrounds, and cameras, then finetuning and deploying zero-shot. Prose uses selective bold emphasis without repeated underlining. It has its own four-task selector: Hang Mug, Arrange Table, Flip and Arrange Shoe, and Pack Battery. Buttons use four columns on wide screens and two in narrow layouts. Hang Mug is selected by default, with exactly one video visible. Selecting another task highlights its button, pauses the previous clip, and resets the selected clip without scrolling or changing the URL. Clicking the current task preserves playback. Arrow Left/Right and Home/End navigate the buttons, with accessible selection states and announcements. This selector operates independently of Agentic Keypoint Programs and RoboTwin. Without JavaScript, the default Hang Mug clip remains available.

All four domain-randomization videos have playback controls and first-frame posters, are centered at up to their native 960-pixel width, and scale to smaller screens while preserving their 960 × 720 resolution, 4:3 aspect ratio, and 50 fps timing. Hang Mug retains the original 5.12-second clip copied from `../Codegen_Blender_Visualization_artifacts/20261008T164407Z/data/visualization/hang_mug/sample_12/planner_d/camera_perspective_1/domain_randomization_camera_4x3/domain_randomization.mp4`. The other three videos are exact copies of `../Codegen_Blender_Visualization/data/domain_randomization/{table_arrange,flip_then_arrange_shoe,pack_battery}/domain_randomization_mujoco.mp4`, each 5 seconds and 250 frames. Their backgrounds, lighting, textures, camera motion, and timing are preserved.

Sim-to-Real Results appears under Technical Details → Data Efficiency and Robustness, before Robotwin Benchmark. It displays the previous main-results figure from `media/figures/main-results.png`, scaled to the available width with its original aspect ratio. Both the figure and the visible “View PDF” link open the original full-resolution `media/figures/main-results.pdf` in a new tab.

Robotwin Benchmark is a sibling subsection of Data Efficiency and Robustness under Technical Details, with matching heading typography, spacing, and navigation level. It begins with a brief comparison of UniKey and dense sampling on 10 RoboTwin 2.0 tasks. It uses the shared paragraph typography. The ten RoboTwin task buttons form a grid: five columns on wide screens, three in intermediate layouts, and two at 580 pixels or less. Clicking a task immediately shows its matching keypoint video and success-rate curve in the same location. The selected button is highlighted. Repeated task headings, standalone success-rate summaries, the comparison table, and carousel controls are removed.

Only the selected task panel is visible with JavaScript enabled. Switching tasks pauses the previous clip and resets the newly selected clip. Clicking the current task preserves playback. Arrow Left/Right and Home/End navigate tasks when the task picker or visualization region is focused; video progress sliders retain their own keyboard behavior. Task URL fragments support direct links and browser history. Videos pause when they leave view or the page is hidden. Without JavaScript, all video-and-curve panels remain available vertically.

RoboTwin videos retain their original 1440 × 1080 resolution, 50 fps, camera views, keypoint diamonds, and dashed connections. The stage captions are removed from both clips and posters. No text-generation animation is included.

## Editing

- `index.html`: the five blog sections, capability links, technical explanations, real-world rollouts, task demonstrations, and results.
- `assets/site.css`: the ENPIRE-style video opening, serif article, responsive outline, drawer, controls, and media layouts.
- `assets/video-controls.js`: progressive enhancement of all 30 article videos with compact play/pause, speed, progress, video length, and fullscreen controls. Native controls remain the no-JavaScript fallback. Real-world clips default to 30× and cycle through 60× and 100×; other videos retain their original 1× default and speed options. The duration to the right of each timeline adjusts to the selected speed.
- `assets/presentation.js`: opening-video playback and reduced-motion behavior, plus the mobile contents dialog.
- `assets/fonts/`: local Source Serif 4 and its font license.
- `assets/videos/hero/`: the supplied opening video and a first-frame poster.
- `assets/site.js`: task selection, keyboard navigation, history, offscreen video pausing, section navigation, and reading progress.
- `assets/pipeline.js`: independent Agentic Keypoint Programs, Policy Failure Detection and Correction, Policy Improvement, and Domain Randomization task selection without scrolling, selected-button state, playback reset/pausing, and keyboard navigation.
- `assets/videos/pipeline/`: four full-HD v5 live text → shrink → 4×3 replay-grid clips, served as `combined.mp4`, and their first-frame posters, in `hang-mug/`, `arrange-table/`, `flip-and-arrange-shoe/`, and `pack-battery/`.
- `assets/videos/pipeline/failure-detection-correction/`: four v5 task clips served as `{task}/rollout.mp4`, with `{task}/poster.jpg`, plus four policy improvement videos. Hang Mug retains `automatic-corrections-across-rounds.mp4`; the other three use `{task}/training-rounds.mp4` and `{task}/training-rounds-poster.jpg`. The older paired clips are no longer referenced by the page.
- `assets/videos/pipeline/domain-randomization/`: four domain-randomization clips and their first-frame posters.
- `media/robotwin/`: caption-free MuJoCo demonstrations, posters at 0.5 seconds, SVG success-rate curves, and PNG exports.
- `media/figures/main-results.png` and `media/figures/main-results.pdf`: the previous main-results preview and full-resolution PDF, displayed under Sim-to-Real Results.
- `data/visualization-media.json`: dimensions, frame counts, timing, media checksums, and clean-render source checksums for all ten videos.
- `data/robotwin-results.json`: original evaluation counts and archive-relative source paths, plus the source archive SHA-256.
- `scripts/preview.py`: local static preview with byte-range support for video seeking.
- `scripts/update_robotwin.py`: regenerates the curves using task-button labels; it does not recreate a table or result summaries.
- `scripts/update_robotwin_media.py`: recreates keypoint annotations from clean rendered videos and recorded pixel coordinates, omitting stage captions, then refreshes posters, media checksums, and URL cache versions.
- `assets/videos/realworld/`: the four supplied real-world rollouts, with playback controls and `preload="none"`, shown in two columns on desktop and one on mobile.
- `UniKey.pdf`: the updated manuscript supplied as `CodeGen_ICRA-2.pdf`, linked from the Paper button and included in the GitHub Pages bundle.

The current real-world source clips are `/home/yuan/Desktop/{hang_mug,arrange_table,flip_then_arrange_shoe,pack_battery}_w_text.mp4`, including their supplied text overlays. Their web copies are 1920 × 1080 H.264 at 30 fps with original AAC audio, approximately one minute long. They preserve all source frames and timing without trimming, padding, or a final-frame hold. The videos appear under Sim-to-Real → Real-World Execution. The text retains the reported 100% success rate for 30 minutes without real-world demonstrations or policy finetuning.

These clips already encode 30× speed. Their `data-base-speed="30"` attribute makes the controls display 30×, 60×, and 100× while applying file playback rates of 1, 2, and 100/30. The video length at the right end of the timeline updates to approximately 60s, 30s, or 18s. A `data-duration` hint supplies the initial length while `preload="none"` keeps the video deferred; loaded metadata provides the measured duration thereafter. Seeking always uses the original media timeline, so changing speed preserves the current position. Other article videos retain their original speed choices. The older uploads remain locally in ignored `assets/videos/realworld/sources/`.

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

The task-picker test checks the five-section reading order, navigation targets, and technical headings, then exercises both production handlers with a DOM fixture: independent four-task Agentic Keypoint Programs, Policy Failure Detection and Correction, Policy Improvement, and Domain Randomization selectors, Hang Mug defaults, exactly one visible task block per selector, one video per corrective task with matching media and no paired-player captions, policy improvement media and native dimensions, no selection-induced scrolling or navigation, independent RoboTwin selection, matching media paths and domain media files, selected-button state, playback pausing/reset, keyboard behavior, RoboTwin URL fragments/history, offscreen/background pausing, and the removed sections/table/summaries. It does not verify browser layout or decoding. The older `tests/method-demo.py` targets the archived Method demo and is no longer a check for the current page.
