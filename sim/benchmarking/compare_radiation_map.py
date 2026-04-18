###
# Creation of a heatmap of the belief map contructed by DORA
###
import json
import math
from os import listdir
from os.path import isfile, join

import numpy as np
import seaborn as sns

### Parameters
result_folder_frontier = "../results/frontier/"
result_folder_random = "../results/randomwalk/"
result_folder_dora = "../results/dora/"
radiation_sources_folder = "../data/"
figures_folder = "figures/"
number_of_steps_max = 300
map_size = 16
folders = [result_folder_random, result_folder_frontier, result_folder_dora]
###

onlyfiles0 = [
    f for f in listdir(result_folder_dora) if isfile(join(result_folder_dora, f))
]
onlyfiles1 = [
    f for f in listdir(result_folder_dora) if isfile(join(result_folder_dora, f))
]
number_of_runs = int(min(len(onlyfiles0) / 2, len(onlyfiles1) / 2))
number_of_folders = len(folders)

for folder in range(0, number_of_folders):
    print("---Processing folder " + folders[folder] + "---")
    for run in range(0, number_of_runs):
        # Files names
        result_file = folders[folder] + "result" + str(run) + ".csv"
        radiation_sources_file = (
            radiation_sources_folder + "radiation_sources" + str(run) + ".json"
        )
        print("------- RUN " + str(run) + " -------")

        # Read radiation results.
        f = open(result_file, "r")
        result_X = np.array([])
        result_Y = np.array([])
        result_belief = np.array([])
        lines = f.readlines()
        for line in lines:
            elems = line.split(",")
            result_X = np.append(result_X, int(elems[0]))
            result_Y = np.append(result_Y, int(elems[1]))
            result_belief = np.append(result_belief, float(elems[2]))

        # Read the radiation sources
        radiation_X = np.array([])
        radiation_Y = np.array([])
        radiation_intensity = np.array([])
        with open(radiation_sources_file) as json_file:
            data = json.load(json_file)
            for r in data["sources"]:
                radiation_X = np.append(radiation_X, float(r["x"]))
                radiation_Y = np.append(radiation_Y, float(r["y"]))
                radiation_intensity = np.append(
                    radiation_intensity, float(r["intensity"])
                )

        # Plot results
        belief_map = np.zeros((map_size + 1, map_size + 1))
        for i in range(len(result_belief)):
            belief_map[
                int(result_Y[i] + map_size / 2), int(result_X[i] + map_size / 2)
            ] = result_belief[i]

        plot = sns.heatmap(belief_map, xticklabels=5, yticklabels=5, cmap="Blues")
        plot.invert_yaxis()
        plot.scatter(
            radiation_X + map_size / 2,
            radiation_Y + map_size / 2,
            marker="*",
            s=100,
            color="red",
        )

        # Drawing the frame
        for _, spine in plot.spines.items():
            spine.set_visible(True)
            spine.set_linewidth(1)

        # Save heatmap
        plot.figure.savefig(
            figures_folder
            + "heatmap_folder_"
            + str(folder)
            + "_run_"
            + str(run)
            + ".png",
            dpi=200,
        )
        plot.get_figure().clf()  # this clears the figure
