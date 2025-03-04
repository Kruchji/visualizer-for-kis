#!/usr/bin/env python3

import os
import random
import numpy as np

falloffExponent = 0.4   # lower value => later images get selected more

for folderName in os.listdir("./Data/"):

    filenames = os.listdir("./Data/" + folderName + "/")

    weights = np.array([1 / ((i+1) ** falloffExponent) for i in range(len(filenames))])

    # Normalize the weights to sum to 1
    weights /= weights.sum()

    # Sample item based on weights
    chosenTarget = random.choices(filenames, weights=weights, k=1)[0]

    with open("./Data/" + folderName + '/chosenTarget.txt', 'w') as targetFile:
        targetFile.write(chosenTarget)