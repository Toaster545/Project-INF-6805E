#include "maritime_loop_functions.h"

#include <chrono>
#include <fstream>
#include <stdexcept>

/****************************************/
/* File-name constants                  */
/****************************************/

/* Matches the numbering used by the drone controller for result{N}.csv,
   so detections{N}.csv always pairs with the correct experiment run.  */
static const std::string RESULT_FILE    = "results/result";
static const std::string DETECTION_FILE = "results/detections";

/****************************************/
/****************************************/

CMaritimeLoopFunctions::CMaritimeLoopFunctions()
    : CLoopFunctions()
    , m_pcTargetLight(nullptr)
{
    /* Seed RNG from wall-clock time. */
    rng_.seed(static_cast<unsigned>(
        std::chrono::high_resolution_clock::now().time_since_epoch().count()));

    /*
     * Find the next free experiment number by checking which result{N}.csv
     * does not yet exist.  This mirrors the logic in the drone controller so
     * both always agree on the current experiment index.
     */
    int experiment_number = -1;
    std::string probe;
    do {
        ++experiment_number;
        probe = RESULT_FILE + std::to_string(experiment_number) + ".csv";
    } while (std::ifstream(probe).good());

    detection_file_name_ = DETECTION_FILE + std::to_string(experiment_number) + ".csv";
}

/****************************************/
/****************************************/

CMaritimeLoopFunctions::~CMaritimeLoopFunctions() {}

/****************************************/
/****************************************/

void CMaritimeLoopFunctions::Init(TConfigurationNode& t_tree) {
    try {
        TConfigurationNode& tMaritime = GetNode(t_tree, "maritime");

        float target_x, target_y;
        float drift_x, drift_y;
        float noise_std;
        float detection_radius;
        float min_x, min_y, max_x, max_y;

        GetNodeAttribute(tMaritime, "target_x",         target_x);
        GetNodeAttribute(tMaritime, "target_y",         target_y);
        GetNodeAttribute(tMaritime, "drift_x",          drift_x);
        GetNodeAttribute(tMaritime, "drift_y",          drift_y);
        GetNodeAttribute(tMaritime, "noise_std",        noise_std);
        GetNodeAttribute(tMaritime, "detection_radius", detection_radius);

        /* Arena bounds are optional – defaults match the 20 x 20 arena. */
        min_x = -9.5f; min_y = -9.5f;
        max_x =  9.5f; max_y =  9.5f;
        if (NodeAttributeExists(tMaritime, "min_x")) GetNodeAttribute(tMaritime, "min_x", min_x);
        if (NodeAttributeExists(tMaritime, "min_y")) GetNodeAttribute(tMaritime, "min_y", min_y);
        if (NodeAttributeExists(tMaritime, "max_x")) GetNodeAttribute(tMaritime, "max_x", max_x);
        if (NodeAttributeExists(tMaritime, "max_y")) GetNodeAttribute(tMaritime, "max_y", max_y);

        float theta = 0.1f;
        if (NodeAttributeExists(tMaritime, "theta"))
            GetNodeAttribute(tMaritime, "theta", theta);

        target_ = std::make_unique<MaritimeTarget>(
            target_x, target_y,
            drift_x, drift_y,
            noise_std,
            detection_radius,
            theta,
            min_x, min_y, max_x, max_y);

        /* Add a red light entity so the target is visible in Qt-OpenGL. */
        m_pcTargetLight = new CLightEntity(
            "target_light",
            CVector3(target_x, target_y, 0.5f),
            CColor::RED,
            1.0f);
        AddEntity(*m_pcTargetLight);

    } catch (CARGoSException& ex) {
        THROW_ARGOSEXCEPTION_NESTED("Error parsing <maritime> node in loop functions!", ex);
    }
}

/****************************************/
/****************************************/

void CMaritimeLoopFunctions::PostStep() {
    target_->Step(rng_);
    /* Keep the light marker in sync with the target. */
    if (m_pcTargetLight) {
        CVector2 pos = target_->GetPosition();
        m_pcTargetLight->SetPosition(CVector3(pos.GetX(), pos.GetY(), 0.5f));
    }
}

/****************************************/
/****************************************/

void CMaritimeLoopFunctions::LogDetection(UInt32 step, UInt32 robot_id) {
    /* Columns: step, robot_id, target_x, target_y */
    std::ofstream f(detection_file_name_, std::ios::out | std::ios::app);
    CVector2 pos = target_->GetPosition();
    f << step     << ","
      << robot_id << ","
      << pos.GetX() << ","
      << pos.GetY() << "\n";
}

/****************************************/
/****************************************/

REGISTER_LOOP_FUNCTIONS(CMaritimeLoopFunctions, "maritime_loop_functions")
