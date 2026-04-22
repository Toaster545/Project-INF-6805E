#ifndef MARITIME_TARGET_H
#define MARITIME_TARGET_H

#include <cmath>
#include <random>
#include <argos3/core/utility/math/vector2.h>

using namespace argos;

namespace buzz_drone_sim {

/*
 * Represents a single maritime search-and-rescue target that drifts
 * over time due to ocean currents and wind perturbations.
 */
class MaritimeTarget {

public:
    /*
     * @param x, y              Initial position (metres)
     * @param drift_x, drift_y  Mean ocean-current vector (metres/step)
     * @param noise_std         Std-dev of Gaussian noise applied to velocity (metres/step)
     * @param detection_radius  A drone within this radius detects the target
     * @param theta             Ornstein-Uhlenbeck mean-reversion rate [0,1].
     *                          Low values (~0.05) give long, sweeping curves;
     *                          high values (~0.5) snap velocity back quickly.
     * @param min_x .. max_y    Arena bounds – target is clamped inside these
     */
    MaritimeTarget(float x, float y,
                   float drift_x, float drift_y,
                   float noise_std,
                   float detection_radius,
                   float theta   =  0.1f,
                   float min_x = -9.5f, float min_y = -9.5f,
                   float max_x =  9.5f, float max_y =  9.5f);

    /*
     * Advance one step using an Ornstein-Uhlenbeck velocity model:
     *   v += theta * (drift - v) + noise_std * N(0,1)
     *   pos += v
     * This gives smooth, correlated motion that gradually drifts in the
     * current direction rather than jumping erratically each tick.
     */
    void Step(std::default_random_engine& rng);

    /* Returns true when the drone at (drone_x, drone_y) is within detection_radius. */
    bool IsDetected(float drone_x, float drone_y) const;

    CVector2 GetPosition() const;

private:
    float x_, y_;
    float vx_, vy_;          /* current velocity (initialised to drift) */
    float drift_x_, drift_y_;
    float noise_std_;
    float theta_;            /* O-U mean-reversion rate */
    float detection_radius_;
    float min_x_, min_y_, max_x_, max_y_;
};

} // namespace buzz_drone_sim

#endif // MARITIME_TARGET_H
