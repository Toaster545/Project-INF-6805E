###
# Maritime SAR metrics: compare randomwalk_maritime vs dora_maritime.
#
# Input files (per run N in each result folder):
#   detections{N}.csv    — step, robot_id, target_x, target_y
#   result{N}.csv        — x, y, belief, weight, step, robot_id
#   data_transmitted{N}.csv — total_data, step, robot_id
#
# Metrics computed:
#   1. Time to first detection (TTD) — minimum step in detections file
#   2. Cumulative detections over time — detection events accumulated per step
#   3. Re-detection rate over time — fraction of steps [0..t] with >=1 detection
#   4. Coverage over time — cumulative unique grid cells visited per step
#   5. Data transmitted per robot over time
###

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")
### Parameters
import os
from os import listdir
from os.path import exists, isfile, join

import numpy as np

result_folder_randomwalk = "../results/randomwalk_maritime/"
result_folder_dora_baseline = "../results/dora_baseline_maritime/"
result_folder_dora = "../results/dora_maritime/"
figures_folder = "figures/"

# print(f"Current Working Directory: {os.getcwd()}")
os.makedirs(figures_folder, exist_ok=True)

NUMBER_OF_STEPS = 300  # must match experiment length in .argos
###

FOLDERS = [result_folder_randomwalk, result_folder_dora_baseline, result_folder_dora]
LABELS = ["Random Walk", "DORA Baseline", "DORA Maritime (improved)"]
COLORS = ["lightcoral", "gold", "cornflowerblue"]


def count_runs(folder):
    """Return number of complete run pairs (detections + result files)."""
    if not exists(folder):
        return 0
    files = [f for f in listdir(folder) if isfile(join(folder, f))]
    det_count = sum(
        1 for f in files if f.startswith("detections") and f.endswith(".csv")
    )
    return det_count


def read_detections(path):
    """
    Returns array of shape (n_events, 4): [step, robot_id, target_x, target_y].
    Returns empty array if file missing or empty.
    """
    rows = []
    if not exists(path):
        return np.empty((0, 4))
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 4:
                continue
            rows.append(
                [float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])]
            )
    return np.array(rows) if rows else np.empty((0, 4))


def read_coverage(path):
    """
    Returns sorted array of steps at which each new cell was first logged
    (i.e., the step column of result{N}.csv).
    """
    if not exists(path):
        return np.array([])
    steps = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 5:
                continue
            steps.append(float(parts[4]))
    return np.array(steps)


def read_data_transmitted(path):
    """
    Returns dict: {step -> total_data_sum_across_robots}.
    Each line: total_data, step, robot_id.
    We accumulate total_data per step (one entry per robot per step).
    """
    if not exists(path):
        return {}
    per_step = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 3:
                continue
            total_data = float(parts[0])
            step = int(float(parts[1]))
            per_step[step] = per_step.get(step, 0.0) + total_data
    return per_step


# ──────────────────────────────────────────────────────────────
# Collect per-run data for each folder
# ──────────────────────────────────────────────────────────────

number_of_runs = min(count_runs(f) for f in FOLDERS)
if number_of_runs == 0:
    print("No completed runs found. Run experiments first.")
    exit(1)

print(f"Processing {number_of_runs} runs per folder.")

# Arrays indexed [folder, run, step]
ttd = np.full((len(FOLDERS), number_of_runs), np.nan)
cumulative_detections = np.zeros((len(FOLDERS), number_of_runs, NUMBER_OF_STEPS))
redetection_rate = np.zeros((len(FOLDERS), number_of_runs, NUMBER_OF_STEPS))
coverage = np.zeros((len(FOLDERS), number_of_runs, NUMBER_OF_STEPS))
data_transmitted = np.zeros((len(FOLDERS), number_of_runs, NUMBER_OF_STEPS))

for fi, folder in enumerate(FOLDERS):
    print(f"--- {folder} ---")
    for run in range(number_of_runs):
        det_file = folder + f"detections{run}.csv"
        res_file = folder + f"result{run}.csv"
        data_file = folder + f"data_transmitted{run}.csv"

        # ── Detections ──────────────────────────────────────────
        det = read_detections(det_file)
        if det.shape[0] > 0:
            steps_with_detection = det[:, 0].astype(int)

            # Time to first detection
            ttd[fi, run] = steps_with_detection.min()

            # Cumulative detection count and re-detection rate
            det_count = 0
            steps_detected = set()
            for s in range(NUMBER_OF_STEPS):
                mask = steps_with_detection == s
                if mask.any():
                    det_count += mask.sum()
                    steps_detected.add(s)
                cumulative_detections[fi, run, s] = det_count
                # Re-detection rate: fraction of elapsed steps with >=1 detection
                redetection_rate[fi, run, s] = len(steps_detected) / (s + 1)

        # ── Coverage (unique cells over time) ───────────────────
        cov_steps = read_coverage(res_file)
        if cov_steps.size > 0:
            cell_count = 0
            for s in range(NUMBER_OF_STEPS):
                cell_count += (cov_steps == s).sum()
                coverage[fi, run, s] = cell_count

        # ── Data transmitted ────────────────────────────────────
        dt_map = read_data_transmitted(data_file)
        running = 0.0
        for s in range(NUMBER_OF_STEPS):
            running += dt_map.get(s, 0.0)
            data_transmitted[fi, run, s] = running


# ──────────────────────────────────────────────────────────────
# Print summary statistics
# ──────────────────────────────────────────────────────────────

print("\n=== Summary ===")
for fi, label in enumerate(LABELS):
    valid_ttd = ttd[fi][~np.isnan(ttd[fi])]
    detected_runs = len(valid_ttd)
    mean_ttd = np.mean(valid_ttd) if detected_runs > 0 else float("nan")
    std_ttd = np.std(valid_ttd) if detected_runs > 0 else float("nan")

    final_redet = redetection_rate[fi, :, NUMBER_OF_STEPS - 1]
    mean_redet = np.nanmean(final_redet)
    std_redet = np.nanstd(final_redet)

    final_cov = coverage[fi, :, NUMBER_OF_STEPS - 1]
    mean_cov = np.nanmean(final_cov)

    print(f"\n{label}:")
    print(f"  Runs with detection : {detected_runs}/{number_of_runs}")
    print(f"  TTD mean ± std      : {mean_ttd:.1f} ± {std_ttd:.1f} steps")
    print(f"  Re-detection rate   : {mean_redet:.3f} ± {std_redet:.3f}")
    print(f"  Final coverage      : {mean_cov:.0f} cells")


# ──────────────────────────────────────────────────────────────
# Plots
# ──────────────────────────────────────────────────────────────

x_axis = np.arange(NUMBER_OF_STEPS)


def plot_metric(data, ylabel, filename, use_log=False):
    fig, ax = plt.subplots()
    for fi in range(len(FOLDERS)):
        mean = data[fi].mean(axis=0)
        std = 0.5 * data[fi].std(axis=0)
        ax.plot(x_axis, mean, color=COLORS[fi], label=LABELS[fi])
        ax.fill_between(x_axis, mean - std, mean + std, alpha=0.25, color=COLORS[fi])
    if use_log:
        ax.set_yscale("log")
    ax.set_xlabel("Step")
    ax.set_ylabel(ylabel)
    ax.legend()
    plt.tight_layout()
    plt.savefig(figures_folder + filename)
    plt.close()


plot_metric(cumulative_detections, "Cumulative detections", "cumulative_detections.png")

plot_metric(
    redetection_rate,
    "Re-detection rate (fraction of steps with contact)",
    "redetection_rate.png",
)

plot_metric(coverage, "Cumulative cells explored", "coverage.png")

plot_metric(
    data_transmitted / 1000.0, "Data transmitted per robot (kB)", "transmitted.png"
)


# TTD distribution (box plot)
fig, ax = plt.subplots()
valid = [ttd[fi][~np.isnan(ttd[fi])] for fi in range(len(FOLDERS))]
ax.boxplot(
    valid,
    labels=LABELS,
    patch_artist=True,
    boxprops=dict(facecolor="white"),
    medianprops=dict(color="black"),
)
for fi, v in enumerate(valid):
    jitter = np.random.uniform(-0.1, 0.1, size=len(v))
    ax.scatter(
        np.full(len(v), fi + 1) + jitter, v, color=COLORS[fi], alpha=0.6, zorder=3
    )
ax.set_ylabel("Step of first detection")
ax.set_title("Time to First Detection")
plt.tight_layout()
plt.savefig(figures_folder + "ttd_distribution.png")
plt.close()

print(f"\nFigures saved to {figures_folder}")
