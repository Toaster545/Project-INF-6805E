"""
Runs multiple headless ARGoS maritime experiments.

Before running:
  - Comment out the <visualization> block in the target .argos file.
  - Set SCENARIO to one of: 'dora', 'dora_baseline', 'randomwalk'
  - Results land in results/<SCENARIO>_maritime/

Scenarios:
  dora          — improved DORA with tracker/explorer split (maritime.argos)
  dora_baseline — plain DORA exploration, no sighting (dora_baseline_maritime.argos)
  randomwalk    — random walk baseline (randomwalk_maritime.argos)
"""

import os
import shutil
import subprocess
import time

# ── Configuration ──────────────────────────────────────────────
SCENARIO = "dora"  # "dora", "dora_baseline", or "randomwalk"
NB_RUNS = 10
PARALLEL = True
STAGGER_DELAY = 2  # seconds between process launches (avoid seed collision)
# ──────────────────────────────────────────────────────────────

ARGOS_FILES = {
    "dora":          "maritime.argos",
    "dora_baseline": "dora_baseline_maritime.argos",
    "randomwalk":    "randomwalk_maritime.argos",
}
if SCENARIO not in ARGOS_FILES:
    raise ValueError(f"Unknown scenario '{SCENARIO}'. Choose from: {list(ARGOS_FILES)}")

ARGOS_FILE = ARGOS_FILES[SCENARIO]
RESULT_DIR = f"../results/{SCENARIO}_maritime/"

os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs("results", exist_ok=True)


def move_results(run_index):
    """Move result files produced by run N into the scenario subfolder."""
    for prefix in ("detections", "result", "data_transmitted"):
        src = f"results/{prefix}{run_index}.csv"
        dst = f"{RESULT_DIR}{prefix}{run_index}.csv"
        if os.path.exists(src):
            shutil.move(src, dst)


def main():
    command = [f"argos3 -c {ARGOS_FILE}"]
    print(f"Scenario  : {SCENARIO}")
    print(f"Config    : {ARGOS_FILE}")
    print(f"Output dir: {RESULT_DIR}")
    print(f"Runs      : {NB_RUNS}\n")

    if PARALLEL:
        processes = []
        for i in range(NB_RUNS):
            p = subprocess.Popen(
                command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            processes.append(p)
            print(f"Started run #{i}  (pid {p.pid})")
            time.sleep(STAGGER_DELAY)

        for i, p in enumerate(processes):
            _, stderr = p.communicate()
            if p.returncode != 0:
                print(f"Run #{i} FAILED (code {p.returncode})")
                if stderr:
                    print(stderr.decode()[-500:])
            else:
                print(f"Run #{i} finished OK")
            move_results(i)
    else:
        for i in range(NB_RUNS):
            p = subprocess.Popen(
                command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            _, stderr = p.communicate()
            if p.returncode != 0:
                print(f"Run #{i} FAILED (code {p.returncode})")
                if stderr:
                    print(stderr.decode()[-500:])
            else:
                print(f"Run #{i} finished OK")
            move_results(i)

    print(f"\nAll runs complete. Results in {RESULT_DIR}")


if __name__ == "__main__":
    main()
