#ifndef MARITIME_LOOP_FUNCTIONS_H
#define MARITIME_LOOP_FUNCTIONS_H

#include "../../../controller/src/argos/maritime_target.h"

#include <argos3/core/simulator/loop_functions.h>
#include <argos3/core/simulator/simulator.h>
#include <argos3/plugins/simulator/entities/light_entity.h>

#include <memory>
#include <random>
#include <string>

using namespace argos;
using namespace buzz_drone_sim;

/*
 * Loop function for the maritime SAR scenario.
 *
 * Responsibilities:
 *  - Owns and steps the MaritimeTarget each simulation tick (PostStep).
 *  - Exposes GetTarget() so the drone controller can query detection.
 *  - Logs the discovery step/robot to results/discovery{N}.csv the first
 *    time any robot reports finding the target (NotifyDiscovery).
 */
class CMaritimeLoopFunctions : public CLoopFunctions {

public:
    CMaritimeLoopFunctions();
    virtual ~CMaritimeLoopFunctions();

    virtual void Init(TConfigurationNode& t_tree);

    /* Called by ARGoS after every robot step – advances the target position. */
    virtual void PostStep();

    /* Controller queries this to check whether it is within detection range. */
    const MaritimeTarget& GetTarget() const { return *target_; }

    /* Log every detection event for re-detection metrics. */
    void LogDetection(UInt32 step, UInt32 robot_id);

private:
    std::unique_ptr<MaritimeTarget> target_;
    std::default_random_engine rng_;

    /* Visual marker: a red light that follows the target. */
    CLightEntity* m_pcTargetLight;

    std::string detection_file_name_;  /* logs every detection for re-detection metric */
};

#endif // MARITIME_LOOP_FUNCTIONS_H
