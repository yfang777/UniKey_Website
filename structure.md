# UniKey Blog Structure

The website keeps the agreed reading order below. Its visual design follows ENPIRE: a video opening with top-centered phase captions, cream background, serif typography, and an article outline with a mobile contents drawer. These notes remain open for discussion in chat.

## Lessons from the references

- [Atlas](https://www.worldlabs.ai/blog/atlas): introduce capabilities and examples before architecture. Explain what readers should notice, use accessible section titles, and leave deeper technical details for later.
- [ENPIRE](https://research.nvidia.com/labs/gear/enpire/#enpire-system): make evidence inspectable through rollouts, failure traces, system explanations, and comparisons. Explain the evaluation conditions beside headline metrics.
- Use Atlas as the structural reference for UniKey: introduction, capability sections with demonstrations, then technical details. Follow ENPIRE's visual design throughout, while retaining this reading order and UniKey's content.

## Central message

The same keypoint programs support demonstration generation, policy failure detection, and corrective data collection. This shared interface should connect the story across the pipeline.

Possible title: **UniKey: From Keypoint Programs to Robust Robot Policies**.

## Reading Order

### 1. Introducing UniKey

Briefly introduce the challenge, the shared keypoint interface, and UniKey's main capabilities. Give readers an overview before explaining individual stages.

### 2. Expert Data Generation

Show how UniKey generates demonstrations from keypoint programs across different object initializations. Lead with the capability and examples; keep detailed mechanics for Technical Details.

### 3. Automated Detection and Correction of Failure

Show a policy failure and the resulting corrective data. Explain the cycle of policy rollout, corrective data generation, and policy finetuning at a high level.

### 4. Sim-to-Real

Explain domain randomization and zero-shot deployment. Show real-world executions, with evaluation conditions beside the results.

### 5. Technical Details

After the capability demonstrations, explain the underlying mechanisms and quantitative evidence.

#### Policy Failure Detection and Correction

Explain how the keypoint program monitors execution, detects deviations, and supplies corrective motion planning. Connect the mechanism to the examples in Automated Detection and Correction of Failure.

#### Data Efficiency and Robustness

Explain why corrective data helps, then present the comparison with dense sampling and the relevant sim-to-real results. Introduce each figure with the question it answers and state its main takeaway.

#### Robotwin Benchmark

Compare UniKey and dense sampling across the 10 RoboTwin tasks, with task-selectable demonstrations and success-rate curves. Use the same heading format as Data Efficiency and Robustness.

Keep data budgets, evaluation settings, and metric definitions close to the claims they qualify. Reconcile the manuscript and website results before choosing headline numbers.

## Writing and visual principles

- Keep the narrative compact and preserve the author's logic, following `narrative.md`.
- Use one task to connect the explanation, with other tasks demonstrating breadth.
- Give each visual one purpose: introduce the question, show the evidence, explain the observation.
- Prefer short paragraphs, descriptive headings, and occasional bold emphasis. Reduce repeated underlining.
- State trial counts, execution duration, success definitions, and retry conditions where relevant. Make sure video labels accurately describe the footage shown.
- Keep detailed technical material available after the main explanation.

## Working together

Discuss and revise the central message, section order, and wording here in chat. Update these notes as decisions are made. Draft prose or change the website when requested.
