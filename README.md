# Maritime SAR DORA

An extension of [DORA-Explorer](https://github.com/lajoiepy/DORA-Explorer) for **Maritime Search and Rescue (SAR)** scenarios with drifting targets.

This project adapts the Distributed Online Resource Allocation (DORA) algorithm for maritime SAR, where targets drift due to ocean currents and wind. It includes:

- **Drift-aware navigation**: Robots incorporate ocean drift priors into their exploration
- **Target tracking**: Two-layer sighting system with velocity estimation for re-acquisition
- **Ornstein-Uhlenbeck target model**: Realistic smooth drifting motion for SAR targets
- **Benchmark comparison**: Metrics to compare DORA Maritime vs baseline approaches

## Algorithms

| Algorithm | File | Description |
|-----------|------|-------------|
| **DORA Maritime** | `dora_maritime.bzz` | Improved DORA with tracker/explorer split and velocity prediction |
| **DORA Baseline** | `dora_baseline_maritime.bzz` | Standard DORA exploration with drift bias only |
| **Random Walk** | `randomwalk_maritime.bzz` | Random walk baseline for comparison |

## Project Structure

```
maritime-sar-dora/
├── README.md
├── docker/
│   ├── Dockerfile              # Builds complete environment with ARGoS, Buzz, and maritime extensions
│   └── docker-compose.yml      # Docker Compose configuration
├── sim/
│   ├── algorithms/             # Buzz swarm algorithms
│   │   ├── dora_maritime.bzz
│   │   ├── dora_baseline_maritime.bzz
│   │   └── randomwalk_maritime.bzz
│   ├── scenarios/              # ARGoS simulation configs
│   │   ├── maritime.argos
│   │   ├── dora_baseline_maritime.argos
│   │   └── randomwalk_maritime.argos
│   ├── config/
│   │   └── parameters.bzz      # Experiment parameters (drift, gains, etc.)
│   ├── cpp/                    # C++ extensions to base DORA
│   │   ├── controller/
│   │   │   ├── maritime_target.h/cpp
│   │   │   └── *.patch
│   │   └── loop_functions/
│   │       ├── maritime_loop_functions.h/cpp
│   │       └── CMakeLists.patch
│   ├── benchmarking/           # Analysis scripts
│   │   ├── compute_metrics.py
│   │   └── maritime_radiation_map.py
│   └── run.py                  # Batch experiment runner
└── figures/                    # Generated result plots
```

## Quick Start

### Prerequisites

- Docker
- X11 server (for visualization)
- If you have an nvidia graphics card, you can uncomment the "runtime" and "deploy" sections in the docker-compose.yml file.

### 1. Build and start the container

```bash
cd docker

# Allow X11 forwarding (for visualization)
xhost +local:docker

# Build the image (this takes ~10-15 minutes the first time)
docker compose build

# Start the container
docker compose up -d
```

### 2. Enter the container

```bash
docker exec -it argos_project bash
```

### 3. Run a simulation

```bash
# Run with visualization (default)
argos3 -c maritime.argos
argos3 -c dora_baseline_maritime.argos
argos3 -c randomwalk_maritime.argos
```

## Running Batch Experiments

For headless batch experiments, first comment out the `<visualization>` block in the `.argos` file, then use the batch runner:

```bash
# Edit run.py to select scenario: "dora", "dora_baseline", or "randomwalk"
python3 run.py
```

Results are saved to `results/<scenario>_maritime/`.

## Analyzing Results

After running experiments for all three algorithms:

```bash
cd benchmarking
python3 compute_metrics.py
```

This generates comparison figures:
- `cumulative_detections.png` - Detection count over time
- `redetection_rate.png` - Fraction of steps with target contact
- `coverage.png` - Cells explored over time
- `transmitted.png` - Communication bandwidth used
- `ttd_distribution.png` - Time to first detection distribution

## Configuration

### Maritime target parameters (`scenarios/maritime.argos`)

```xml
<maritime target_x="0.0"        <!-- Initial target position -->
          target_y="0.0"
          drift_x="0.02"        <!-- Ocean current (m/step) -->
          drift_y="0.0"
          noise_std="0.01"      <!-- Wind/wave noise -->
          theta="0.1"           <!-- Ornstein-Uhlenbeck mean-reversion -->
          detection_radius="1.0" />
```

### Algorithm parameters (`config/parameters.bzz`)

```buzz
DRIFT_X    = 0.02   # Robot's prior estimate of drift (must match .argos)
DRIFT_Y    = 0.0
DRIFT_GAIN = 0.5    # Weight of drift bias vs exploration

SIGHTING_GAIN    = 1.5   # Weight of sighting direction
SIGHTING_DECAY   = 150   # Steps until sighting is stale
SIGHTING_MIN_GAP = 20    # Min steps between sightings for velocity estimation
EXPLORER_BOOST   = 1.5   # Exploration boost when sighting exists
```

### X11 display issues

Make sure to run `xhost +local:docker` before starting the container, and ensure the `DISPLAY` environment variable is set correctly.

### modifications to C++ code
To recompile the cpp code you modified under /workspace, you might have to update the version under DBM-SMS.


## License

Based on [DORA-Explorer](https://github.com/lajoiepy/DORA-Explorer) by Pierre-Yves Lajoie.
