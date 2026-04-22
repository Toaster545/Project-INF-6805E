#include "maritime_target.h"

namespace buzz_drone_sim {

/****************************************/
/****************************************/

MaritimeTarget::MaritimeTarget(float x, float y,
                               float drift_x, float drift_y,
                               float noise_std,
                               float detection_radius,
                               float theta,
                               float min_x, float min_y,
                               float max_x, float max_y)
    : x_(x), y_(y),
      vx_(drift_x), vy_(drift_y),   /* start at steady-state drift velocity */
      drift_x_(drift_x), drift_y_(drift_y),
      noise_std_(noise_std),
      theta_(theta),
      detection_radius_(detection_radius),
      min_x_(min_x), min_y_(min_y),
      max_x_(max_x), max_y_(max_y) {}

/****************************************/
/****************************************/

void MaritimeTarget::Step(std::default_random_engine& rng) {
    std::normal_distribution<float> noise(0.0f, noise_std_);

    /* Ornstein-Uhlenbeck velocity update:
     *   v += theta * (drift - v) + sigma * N(0,1)
     * The velocity decays toward the mean current (drift_x, drift_y)
     * with gentle stochastic perturbations, producing smooth curves
     * instead of the erratic per-step position noise. */
    vx_ += theta_ * (drift_x_ - vx_) + noise(rng);
    vy_ += theta_ * (drift_y_ - vy_) + noise(rng);

    x_ += vx_;
    y_ += vy_;

    /* Reflect off arena bounds so the target reverses rather than sticking. */
    if (x_ < min_x_) { x_ = min_x_; vx_ = std::abs(vx_); }
    if (x_ > max_x_) { x_ = max_x_; vx_ = -std::abs(vx_); }
    if (y_ < min_y_) { y_ = min_y_; vy_ = std::abs(vy_); }
    if (y_ > max_y_) { y_ = max_y_; vy_ = -std::abs(vy_); }
}

/****************************************/
/****************************************/

bool MaritimeTarget::IsDetected(float drone_x, float drone_y) const {
    float dist = std::sqrt(std::pow(drone_x - x_, 2.0f) +
                           std::pow(drone_y - y_, 2.0f));
    return dist <= detection_radius_;
}

/****************************************/
/****************************************/

CVector2 MaritimeTarget::GetPosition() const {
    return CVector2(x_, y_);
}

/****************************************/
/****************************************/

} // namespace buzz_drone_sim
