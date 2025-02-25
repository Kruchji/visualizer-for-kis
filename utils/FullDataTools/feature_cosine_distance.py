#!/usr/bin/env python3

import os, shutil
import numpy as np
import csv
from sklearn.metrics.pairwise import cosine_similarity


embeddings = []
with open('GeneratedCLIPFeatures.csv', 'r') as f:
    reader = csv.reader(f, delimiter=';')
    for i, row in enumerate(reader):
        embeddings.append(list(map(float, row)))
        
        embeddings[i] /= np.linalg.norm(embeddings[i])

embeddings2 = []
with open('CLIPFeatures.csv', 'r') as f:
    reader = csv.reader(f, delimiter=';')
    for i, row in enumerate(reader):
        embeddings2.append(list(map(float, row)))
        
        embeddings2[i] /= np.linalg.norm(embeddings2[i])
    


embeddings = np.array(embeddings)
embeddings2 = np.array(embeddings2)

#print(embeddings)
#print(embeddings.shape)

repres_emb = embeddings[0]
repres_emb2 = embeddings2[0]

# Cosine similarity: (A . B) / (||A|| * ||B||)
print("\nMy generated embeddings:")
similarities = np.dot(embeddings, repres_emb) / (np.linalg.norm(embeddings, axis=1) * np.linalg.norm(repres_emb))
print(similarities)

print("\nProvided embeddings:")
similarities2 = np.dot(embeddings2, repres_emb2) / (np.linalg.norm(embeddings2, axis=1) * np.linalg.norm(repres_emb2))
print(similarities2)

#prebuilt_similarities = cosine_similarity(embeddings, [repres_emb])
#print(prebuilt_similarities)