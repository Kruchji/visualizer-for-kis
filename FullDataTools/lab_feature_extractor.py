#!/usr/bin/env python3

import cv2
import numpy as np
import os

main_folder = './new_datasets/'

# Get folders inside main_folder
subfolders = [f.path for f in os.scandir(main_folder) if f.is_dir()]

# For each folder, get the image paths, for each get LAB features and all store in LABFeatures.csv (one line per image, each line containing float values separated by ';')
for subfolder in subfolders:
    print(f"Processing {subfolder}...")

    image_paths = [os.path.join(subfolder, f) for f in os.listdir(subfolder) if f.endswith('.jpg')]
    image_paths.sort()

    lab_features = []
    for img_path in image_paths:
        img = cv2.imread(img_path)
        image_lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        mean_lab = np.mean(image_lab, axis=(0, 1))
        lab_features.append(mean_lab)

    lab_features = np.array(lab_features)
    lab_features = lab_features.reshape(lab_features.shape[0], -1)

    # Save LAB features to CSV
    csv_path = os.path.join(subfolder, 'LABFeatures.csv')
    with open(csv_path, 'w') as f:
        for row in lab_features:
            f.write(';'.join(map(str, row)))
            f.write('\n')
