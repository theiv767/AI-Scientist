import json
import os
import os.path as osp

import matplotlib.pyplot as plt
import numpy as np

# LOAD FINAL RESULTS:
folders = os.listdir("./")
final_results = {}
for folder in folders:
    if folder.startswith("run") and osp.isdir(folder):
        with open(osp.join(folder, "final_info.json"), "r") as f:
            final_results[folder] = json.load(f)

# Plot 1
plt.figure(figsize=(10, 6))
labels = {
    "run_0": "Baseline",
}

#plots
for i, run in enumerate(final_results.keys()):
    pass
    
