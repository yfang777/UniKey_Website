# Success-rate statistics

Open `index.html` or visit `http://127.0.0.1:8000/data_stat/` while the repository preview server is running. `plots/overview.png` compares the four requested tasks; each task also has PNG and SVG exports. Hang Mug's real-world results have a separate plot.

`statistics.json` contains normalized rates, dataset budgets, numerators, denominators, source paths and hashes. `summary.json` contains coverage, final rates and best observed checkpoints. `sources.json` lists every original source file, its remote location, byte count and SHA-256. Original files are preserved unchanged under `raw/`.

| Task | UniKey simulation checkpoints | Dense Sampling simulation checkpoints | Source |
| --- | ---: | ---: | --- |
| Hang Mug | 18 | 39 | robo02: `/local/robopil/yuan/scripts/main_figure/ACT_hang_mug/success_rate_sim.csv` |
| Arrange Table | 0 | 0 | robo02: `/local/robopil/yuan/tasks/table_arrange` |
| Flip and Arrange Shoe | 18 | 1 | robo02: `/local/robopil/yuan/tasks/flip_then_arrange_shoe` |
| Pack Battery | 15 | 15 | robo02: `/local/robopil/yuan/tasks/pack_battery` |

Hang Mug also has two real-world checkpoints for each method. Its CSVs contain rates rather than raw episode outcomes. The source plotting script declares 100 simulation rollouts and 20 real-world rollouts per point; the corresponding integer success counts are reconstructed from those rates and explicitly marked as such. The supplied source plot connects the UniKey simulation curve to Dense Sampling's initial 2k/8% evaluation. The local preview reproduces that connection without adding a measurement row to the original UniKey statistics.

The other tasks use ACT seed 1 with RGB observations and absolute actions. Dense Sampling is read from `dense_sample/rgb_abs_action/dataset_step_*/ACT_rollout_seed_1/dataset_step_*_test_rollout/info.json`. UniKey is read from `v20/{task}_pos_0p02_time_3/rgb_abs_action/ACT_seed_1/rollouts/dataset_step_*_test_rollout/info.json`. Rates are recomputed as the number of episodes whose evaluation status is `success`, divided by the total recorded episodes. All available measured checkpoints are retained, including decreases in success rate.

Arrange Table has no evaluation records in the specified robo02 directory. Its missing-data panel is not a zero success rate. Shoe's canonical Dense Sampling directory contains only the 5k evaluation. Pack Battery's 5k rollout directory is empty, and its 21k directory contains a checkpoint without an evaluation. These unavailable results are not interpolated or borrowed from another experiment.

Four additional Shoe evaluations were found in the separate `tmp_flip_then_arrange_shoe` and `tmp_flip_then_arrange_shoe_298` experiments. Their base/finetuned success rates are 90%/92% and 95%/97%, respectively, each over 100 recorded episodes. Their summaries were checked against every episode outcome. They are included as supplementary statistics and are not labeled as Dense Sampling versus UniKey or combined with the canonical v20 curve.

The plots use the current RoboTwin colors, equal solid lines, small checkpoint markers, regular direct labels and a borderless gold star at the best UniKey checkpoint. Pale shapes show the central 95% exact empirical bootstrap distribution of binary rollout means, `Binomial(n, successes/n)/n`. They describe evaluation sampling uncertainty rather than training-seed variation. At 0% or 100%, the empirical bootstrap distribution is a point and no violin is drawn.

Refresh the source files and then redraw locally:

```sh
python3 scripts/extract_success_statistics.py
python3 scripts/plot_success_statistics.py
```

The first command only reads robo02. The second works offline from the saved extracts. Neither command changes the main website, existing videos, or existing animation data.
