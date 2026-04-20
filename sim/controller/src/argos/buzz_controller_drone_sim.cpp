#include "buzz_controller_drone_sim.h"
#include "../../../loop_functions/src/argos/maritime_loop_functions.h"

#include <iostream>
#include <stdlib.h>
#include <fstream>
#include <stdio.h>
#include <sstream>
#include <algorithm>
#include <cmath>
#include <json/json.h>

#include <argos3/core/simulator/simulator.h>

namespace buzz_drone_sim {

const std::string RESULT_FILE           = "results/result";
const std::string RADIATION_SOURCES_FILE = "data/radiation_sources";
const std::string DATA_TRANSMITTED_FILE = "results/data_transmitted";

/****************************************/
/****************************************/

CBuzzControllerDroneSim::CBuzzControllerDroneSim() : CBuzzControllerKheperaIV() {
   std::chrono::high_resolution_clock::time_point previous = 
      std::chrono::high_resolution_clock::now();
   usleep(10);
   std::chrono::high_resolution_clock::duration duration(
      std::chrono::high_resolution_clock::now() -  previous);
   random_engine_.seed(duration.count());

   // All robots in the same run share one experiment number, computed once.
   static int experiment_number = -1;
   if (experiment_number == -1) {
      experiment_number = 0;
      while (std::ifstream(RESULT_FILE + std::to_string(experiment_number) + ".csv").good()) {
         ++experiment_number;
      }
   }
   result_file_name_         = RESULT_FILE          + std::to_string(experiment_number) + ".csv";
   data_transmitted_file_name_ = DATA_TRANSMITTED_FILE + std::to_string(experiment_number) + ".csv";
   radiation_file_name_      = RADIATION_SOURCES_FILE + std::to_string(experiment_number) + ".json";
   target_found_ = false;
}

/****************************************/
/****************************************/

CBuzzControllerDroneSim::~CBuzzControllerDroneSim() {
}

/****************************************/
/****************************************/

void CBuzzControllerDroneSim::Init(TConfigurationNode& t_node)  {
   CBuzzControllerKheperaIV::Init(t_node);
   result_file_.open(result_file_name_, std::ios::out | std::ios::app);
   data_transmitted_file_.open(data_transmitted_file_name_, std::ios::out | std::ios::app);
}

/****************************************/
/****************************************/

bool CBuzzControllerDroneSim::HasReached(const CVector2& position, const float& delta) {
   float difference = std::sqrt(
      std::pow(m_pcPos->GetReading().Position.GetX() - position.GetX(),2)+
      std::pow(m_pcPos->GetReading().Position.GetY() - position.GetY(),2));

   return difference < delta;   
}

/****************************************/
/****************************************/

std::string CBuzzControllerDroneSim::GetCurrentKey(){
   int x = static_cast<int>(std::rint(m_pcPos->GetReading().Position.GetX()));
   int y = static_cast<int>(std::rint(m_pcPos->GetReading().Position.GetY()));
   std::string key = std::to_string(x) + '_' + std::to_string(y);
   return key;
}

/****************************************/
/****************************************/

float CBuzzControllerDroneSim::GetRadiationIntensity(){
   Json::Value radiationValues;
   Json::Reader reader;
   std::ifstream radiationFile(radiation_file_name_);

   reader.parse(radiationFile, radiationValues);

   if (radiationValues["sources"].size() <= 0){
      throw JSON_USE_EXCEPTION;
   }
   
   int x = static_cast<int>(std::rint(m_pcPos->GetReading().Position.GetX()));
   int y = static_cast<int>(std::rint(m_pcPos->GetReading().Position.GetY()));
   
   float totalRadiationIntensity = 0.0;

   for (auto source : radiationValues["sources"]){
      RadiationSource radiation = RadiationSource(source["x"].asFloat(), source["y"].asFloat(), source["intensity"].asFloat());
      totalRadiationIntensity += radiation.GetPerceivedIntensity(x, y);
   }

   // Normal distribution (mean, std)
   /*std::normal_distribution<float> noise_distribution(0.0, 0.05);
   float noise = noise_distribution(random_engine_);*/

   // Compute belief elem [0,1]
   float radiation_belief = totalRadiationIntensity; // + noise;
   if (radiation_belief < 0.0) {
      radiation_belief = 0.0;
   } else if (radiation_belief > 1.0) {
      radiation_belief = 1.0;
   }

   return radiation_belief;
}

/****************************************/
/****************************************/

float CBuzzControllerDroneSim::GetTargetX() {
   CMaritimeLoopFunctions& lf = dynamic_cast<CMaritimeLoopFunctions&>(
      CSimulator::GetInstance().GetLoopFunctions());
   return lf.GetTargetX();
}

float CBuzzControllerDroneSim::GetTargetY() {
   CMaritimeLoopFunctions& lf = dynamic_cast<CMaritimeLoopFunctions&>(
      CSimulator::GetInstance().GetLoopFunctions());
   return lf.GetTargetY();
}

bool CBuzzControllerDroneSim::IsTargetDetected() {
   CMaritimeLoopFunctions& loop_functions =
      dynamic_cast<CMaritimeLoopFunctions&>(
         CSimulator::GetInstance().GetLoopFunctions());

   float drone_x = m_pcPos->GetReading().Position.GetX();
   float drone_y = m_pcPos->GetReading().Position.GetY();

   bool detected = loop_functions.GetTarget().IsDetected(drone_x, drone_y);

   if (detected) {
      target_found_ = true;
      UInt32 step = CSimulator::GetInstance().GetSpace().GetSimulationClock();
      float robot_x = m_pcPos->GetReading().Position.GetX();
      float robot_y = m_pcPos->GetReading().Position.GetY();
      loop_functions.LogDetection(step, m_unRobotId, robot_x, robot_y);
   }

   return detected;
}

/****************************************/
/****************************************/

void CBuzzControllerDroneSim::LogDatum(const std::string& key, const float& data, const int& step){
   std::string parsed_key = key;
   std::replace(parsed_key.begin(), parsed_key.end(), '_', ' ');
   std::stringstream ss(parsed_key);
   int x, y;
   ss >> x >> y;

   float weight = 1.0;
   result_file_ << x << "," << y << "," << data << "," << weight << "," << step << "," << m_unRobotId << "\n";
   result_file_.flush();
}

/****************************************/
/****************************************/

void CBuzzControllerDroneSim::LogDataSize(const int& total_data, const int& step){
   data_transmitted_file_ << total_data << "," << step << "," << m_unRobotId << "\n";
   data_transmitted_file_.flush();
}

}