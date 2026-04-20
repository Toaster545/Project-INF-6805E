###
# Maritime SAR: visualise where robots think the target is vs where it actually is.
#
# Background heatmap: KDE of robot detection positions (= sighting belief density)
# Red dots          : actual target positions at each detection event
# Blue x markers    : robot positions at detection (what the sighting stigmergy stores)
# Purple lines      : error between belief and reality per detection event
#
# Detection file columns: step, robot_id, target_x, target_y, robot_x, robot_y
###

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from scipy.stats import gaussian_kde
from os.path import exists

### Parameters
result_folder = "../../results/dora_maritime/"
figures_folder = "figures/"
ARENA_HALF    = 8       # exploration stigmergy runs from -8 to +8
NUMBER_OF_STEPS = 300
###

def read_detections(path):
    """
    Returns list of dicts with keys: step, robot_id, target_x, target_y,
    robot_x, robot_y.  Handles both the old 4-column format and the new
    6-column format gracefully.
    """
    rows = []
    if not exists(path):
        return rows
    with open(path) as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 4:
                continue
            row = {
                "step":     float(parts[0]),
                "robot_id": int(float(parts[1])),
                "target_x": float(parts[2]),
                "target_y": float(parts[3]),
                "robot_x":  float(parts[4]) if len(parts) > 4 else None,
                "robot_y":  float(parts[5]) if len(parts) > 5 else None,
            }
            rows.append(row)
    return rows

# ── Find how many runs are available ────────────────────────────────────────
run = 0
available = []
while exists(result_folder + f"detections{run}.csv") or \
      exists(result_folder + f"result{run}.csv"):
    available.append(run)
    run += 1

if not available:
    print(f"No result files found in {result_folder}")
    exit(1)

print(f"Found {len(available)} run(s) in {result_folder} - aggregating all runs")

# ── Collect detections from all runs ─────────────────────────────────────────
all_detections = []
for run in available:
    all_detections.extend(read_detections(result_folder + f"detections{run}.csv"))

if not all_detections:
    print("No detection events found.")
    exit(1)

steps     = np.array([d["step"]     for d in all_detections])
target_xs = np.array([d["target_x"] for d in all_detections])
target_ys = np.array([d["target_y"] for d in all_detections])
have_robot_pos = all_detections[0]["robot_x"] is not None
if have_robot_pos:
    robot_xs = np.array([d["robot_x"] for d in all_detections])
    robot_ys = np.array([d["robot_y"] for d in all_detections])

# ── KDE belief heatmap from robot detection positions ────────────────────────
arena = np.linspace(-ARENA_HALF, ARENA_HALF, 200)
grid_x, grid_y = np.meshgrid(arena, arena)
grid_pts = np.vstack([grid_x.ravel(), grid_y.ravel()])

if have_robot_pos and len(robot_xs) >= 2:
    kde = gaussian_kde(np.vstack([robot_xs, robot_ys]), bw_method=0.4)
    belief_density = kde(grid_pts).reshape(grid_x.shape)
else:
    # Fall back to actual target positions if robot positions unavailable
    kde = gaussian_kde(np.vstack([target_xs, target_ys]), bw_method=0.4)
    belief_density = kde(grid_pts).reshape(grid_x.shape)

# ── Single aggregated figure ─────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 7))

# Belief heatmap
hm = ax.imshow(belief_density, origin="lower", cmap="Blues",
               extent=[-ARENA_HALF, ARENA_HALF, -ARENA_HALF, ARENA_HALF],
               aspect="equal")
plt.colorbar(hm, ax=ax, label="Belief density (robot detections)", shrink=0.7)

# Actual target positions coloured by time
norm = plt.Normalize(0, NUMBER_OF_STEPS)
ax.scatter(target_xs, target_ys, c=cm.Reds(norm(steps)), s=30, zorder=3,
           label="Actual target position")

# Robot detection positions and error lines
if have_robot_pos:
    ax.scatter(robot_xs, robot_ys, c="blue", s=20, marker="x",
               zorder=4, linewidths=1.2, label="Robot belief (sighting)")
    for tx, ty, rx, ry in zip(target_xs, target_ys, robot_xs, robot_ys):
        ax.plot([tx, rx], [ty, ry], color="purple",
                linewidth=0.5, alpha=0.3, zorder=2)

sm = plt.cm.ScalarMappable(cmap="Reds", norm=norm)
sm.set_array([])
plt.colorbar(sm, ax=ax, label="Detection step", shrink=0.7)

ax.set_xlim(-ARENA_HALF, ARENA_HALF)
ax.set_ylim(-ARENA_HALF, ARENA_HALF)
ax.set_xlabel("X (m)")
ax.set_ylabel("Y (m)")
ax.set_title(f"Target belief vs reality - {len(available)} runs aggregated\n"
             f"({len(all_detections)} total detection events)")
ax.legend(loc="upper right", fontsize=8)
plt.tight_layout()

out = figures_folder + "tracker_map_aggregated.png"
plt.savefig(out, dpi=200)
plt.close()
print(f"Saved {out}  ({len(all_detections)} detections across {len(available)} runs)")
