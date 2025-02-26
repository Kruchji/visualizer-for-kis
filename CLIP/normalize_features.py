#!/usr/bin/env python3

import os, shutil
import numpy as np
import csv
from sklearn.metrics.pairwise import cosine_similarity


embeddings = []
with open('CLIPFeatures.csv', 'r') as f:
    reader = csv.reader(f, delimiter=';')
    for i, row in enumerate(reader):
        embeddings.append(list(map(float, row)))
        
        embeddings[i] /= np.linalg.norm(embeddings[i], axis=1, keepdims=True)

# Save the normalized embeddings to a new file
np.savetxt('NormalizedCLIPFeatures.csv', np.array(embeddings), delimiter=';', fmt='%.8e')