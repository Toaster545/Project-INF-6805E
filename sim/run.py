"""
Runs multiple headless ARGoS maritime experiments.

Before running:
  - Comment out the <visualization> block in maritime.argos
  - Set SCENARIO to 'randomwalk' or 'dora' (controls which .argos file is used)
  - Results are written to results/ by the simulation; move them to the
    appropriate subfolder (results/randomwalk_maritime/ or results/dora_maritime/)
    before running the other scenario so files are not overwritten.
"""

import subprocess
import time
import os
import shutil

# ── Configuration ──────────────────────────────────────────────
SCENARIO      = "dora"        # "dora" or "randomwalk"
NB_RUNS       = 10
PARALLEL      = True
STAGGER_DELAY = 2             # seconds between process launches (avoid seed collision)
# ──────────────────────────────────────────────────────────────

ARGOS_FILE = f"{SCENARIO}_maritime.argos" if SCENARIO == "randomwalk" else "maritime.argos"
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
            p = subprocess.Popen(command, shell=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
            p = subprocess.Popen(command, shell=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
