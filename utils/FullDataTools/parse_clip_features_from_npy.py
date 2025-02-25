#!/usr/bin/env python3

import numpy as np

clip_path = 'clip.npy'

clip_data = np.load(clip_path)

print("Loaded clip data:", clip_data)

output_file = "CLIPFeatures.csv"

np.savetxt(output_file, clip_data, delimiter=';', fmt='%.8e')