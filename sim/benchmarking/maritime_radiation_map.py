###
# Maritime SAR: visualise where robots think the target is vs where it actually is.
#
# For each experiment (dora, dora_baseline, randomwalk):
#   - Produces one sample plot every 10 runs (run 0, 10, 20, ...)
#   - Background: smooth KDE heatmap of robot detection positions
#   - Red dots   : actual target positions at each detection event
#   - Blue x     : robot positions at detection
#   - Purple lines: error between belief and reality per detection event
#
# Detection file columns: step, robot_id, target_x, target_y, robot_x, robot_y
###

import matplotlib

matplotlib.use("Agg")
import os
from os.path import exists

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde

### Parameters
RESULT_FOLDERS = {
    "DORA": "../results/dora_maritime/",
    "DORA Baseline": "../results/dora_baseline_maritime/",
    "Random Walk": "../results/randomwalk_maritime/",
}
FIGURES_FOLDER = "figures/"
ARENA_HALF = 8
NUMBER_OF_STEPS = 300
SAMPLE_EVERY = 10  # produce a plot for run 0, 10, 20, ...
###

os.makedirs(FIGURES_FOLDER, exist_ok=True)


def read_detections(path):
    rows = []
    if not exists(path):
        return rows
    with open(path) as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 4:
                continue
            row = {
                "step": float(parts[0]),
                "robot_id": int(float(parts[1])),
                "target_x": float(parts[2]),
                "target_y": float(parts[3]),
                "robot_x": float(parts[4]) if len(parts) > 4 else None,
                "robot_y": float(parts[5]) if len(parts) > 5 else None,
            }
            rows.append(row)
    return rows


def find_available_runs(folder):
    run, available = 0, []
    while exists(folder + f"detections{run}.csv") or exists(
        folder + f"result{run}.csv"
    ):
        available.append(run)
        run += 1
    return available


def make_kde_grid(xs, ys, arena_half=ARENA_HALF, resolution=200, bw=0.4):
    """Return (grid_x, grid_y, density) or None if too few points for KDE."""
    arena = np.linspace(-arena_half, arena_half, resolution)
    grid_x, grid_y = np.meshgrid(arena, arena)

    # Need at least 2 distinct points for KDE
    unique_pts = np.unique(np.vstack([xs, ys]), axis=1)
    if unique_pts.shape[1] < 2:
        return None, None, None

    pts = np.vstack([grid_x.ravel(), grid_y.ravel()])
    xs = xs + np.random.normal(0, 0.01, size=xs.shape)
    ys = ys + np.random.normal(0, 0.01, size=ys.shape)
    kde = gaussian_kde(np.vstack([xs, ys]), bw_method=bw)
    density = kde(pts).reshape(grid_x.shape)
    return grid_x, grid_y, density


def plot_run(run_index, detections, experiment_label, out_path):
    if not detections:
        print(f"  [skip] no detections for run {run_index}")
        return

    steps = np.array([d["step"] for d in detections])
    target_xs = np.array([d["target_x"] for d in detections])
    target_ys = np.array([d["target_y"] for d in detections])
    have_pos = detections[0]["robot_x"] is not None

    fig, ax = plt.subplots(figsize=(8, 7))

    # ── Smooth KDE heatmap ──────────────────────────────────────────────────
    if have_pos:
        robot_xs = np.array([d["robot_x"] for d in detections])
        robot_ys = np.array([d["robot_y"] for d in detections])
        kde_src_x, kde_src_y = robot_xs, robot_ys
    else:
        kde_src_x, kde_src_y = target_xs, target_ys

    # If there is only 1 detection, it produces an error, skip plotting
    if len(kde_src_x) >= 2:
        grid_x, grid_y, density = make_kde_grid(kde_src_x, kde_src_y)
        if density is not None:
            hm = ax.imshow(
                density,
                origin="lower",
                cmap="Blues",
                extent=[-ARENA_HALF, ARENA_HALF, -ARENA_HALF, ARENA_HALF],
                aspect="equal",
                interpolation="bilinear",
                alpha=0.85,
            )
            plt.colorbar(
                hm, ax=ax, label="Belief density (robot detections)", shrink=0.7
            )

    # ── Actual target positions coloured by time ────────────────────────────
    norm = plt.Normalize(0, NUMBER_OF_STEPS)
    ax.scatter(
        target_xs,
        target_ys,
        c=cm.Reds(norm(steps)),
        s=30,
        zorder=3,
        label="Actual target position",
    )

    # ── Robot positions and error lines ────────────────────────────────────
    """
    if have_pos:
        ax.scatter(
            robot_xs,
            robot_ys,
            c="blue",
            s=20,
            marker="x",
            zorder=4,
            linewidths=1.2,
            label="Robot belief (sighting)",
        )
        for tx, ty, rx, ry in zip(target_xs, target_ys, robot_xs, robot_ys):
            ax.plot(
                [tx, rx], [ty, ry], color="purple", linewidth=0.5, alpha=0.3, zorder=2
            )
    """

    # ── Colorbars ───────────────────────────────────────────────────────────
    sm = plt.cm.ScalarMappable(cmap="Reds", norm=norm)
    sm.set_array([])
    plt.colorbar(sm, ax=ax, label="Detection step", shrink=0.7)

    ax.set_xlim(-ARENA_HALF, ARENA_HALF)
    ax.set_ylim(-ARENA_HALF, ARENA_HALF)
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_title(
        f"{experiment_label} — Run {run_index}\n({len(detections)} detection events)"
    )
    ax.legend(loc="upper right", fontsize=8)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"  Saved {out_path}")


# ── Main loop over all experiments ──────────────────────────────────────────
for label, folder in RESULT_FOLDERS.items():
    safe_label = label.lower().replace(" ", "_")
    available = find_available_runs(folder)

    if not available:
        print(f"\n[{label}] No result files found in {folder} — skipping.")
        continue

    print(f"\n[{label}] Found {len(available)} run(s) in {folder}")

    sample_runs = [r for r in available if r % SAMPLE_EVERY == 0]
    print(f"  Producing plots for runs: {sample_runs}")

    exp_figures = os.path.join(FIGURES_FOLDER, safe_label)
    os.makedirs(exp_figures, exist_ok=True)

    for run in sample_runs:
        detections = read_detections(folder + f"detections{run}.csv")
        out_path = os.path.join(exp_figures, f"tracker_map_run{run:03d}.png")
        plot_run(run, detections, label, out_path)

print("\nDone.")
