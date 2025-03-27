#!/usr/bin/env python3

import os, shutil
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
import csv


# Get folders inside extracted_images/mvk_1 and extracted_images/mvk_2
folders = [f.path for f in os.scandir('extracted_images/mvk_1') if f.is_dir()] + [f.path for f in os.scandir('extracted_images/mvk_2') if f.is_dir()]

image_paths = []
embeddings = []

# For each folder, get the image paths and embeddings
for folder in folders:
    added_image_paths = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.jpg')]
    added_image_paths.sort()

    image_paths.extend(added_image_paths)

    # GeneratedCLIPFeatures.csv contains the CLIP embeddings for each image (one line per image, each line containing float values separated by ';')
    # put them in embeddings variable (np.array)
    with open(os.path.join(folder, 'GeneratedCLIPFeatures.csv'), 'r') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            embeddings.append(list(map(float, row)))

embeddings = np.array(embeddings)


# Perform hierarchical clustering (using the 'ward' method)
Z = linkage(embeddings, method='ward')

# Cut the dendrogram to get only 'num_representatives' clusters
num_representatives = 50
labels = fcluster(Z, num_representatives, criterion='maxclust')

# For each cluster, compute the centroid (mean of points in the cluster)
representative_embeddings = []
for i in range(1, num_representatives + 1):
    cluster_points = embeddings[labels == i]
    cluster_centroid = cluster_points.mean(axis=0)
    representative_embeddings.append(cluster_centroid)

representative_embeddings = np.array(representative_embeddings)

# Find the most similar image for each representative embedding
picked_images = []
picked_embeddings = []
for repres_emb in representative_embeddings:
    # Cosine similarity: (A . B) / (||A|| * ||B||)
    similarities = np.dot(embeddings, repres_emb) / (np.linalg.norm(embeddings, axis=1) * np.linalg.norm(repres_emb))
    most_similar_index = np.argsort(similarities)[-1]
    picked_images.append(image_paths[most_similar_index])
    picked_embeddings.append(embeddings[most_similar_index])

# Get the representative images and their embeddings
os.makedirs(f"representative_images", exist_ok=True)

print("Copying representative images")
for i, rep_image in enumerate(picked_images):
    print(f"Representative image {i + 1}: {rep_image}")
    
    old_image_name_parts = os.path.basename(rep_image).split('_')
    new_image_name = f"{i:04}_{old_image_name_parts[1]}_{old_image_name_parts[2]}"

    # Save images to new_datasets folder to folder with i + 1 name (padded to 2 digits)
    shutil.copy(rep_image, f"representative_images/{new_image_name}")

# Also save each embedding on a row to a CSV file - CLIPFeatures.csv
with open(f"representative_images/CLIPFeatures.csv", 'w', newline='') as f:
    writer = csv.writer(f, delimiter=';')
    for emb in picked_embeddings:
        writer.writerow(emb)

# Save names of the representative images to a target_images.txt file
with open(f"representative_images/target_images.txt", 'w') as f:
    for img in picked_images:
        f.write(os.path.normpath(img) + '\n')