#!/usr/bin/env python3

import os, shutil, math
import numpy as np
from sklearn.cluster import KMeans
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import cdist
import csv


# Get folders inside extracted_images/mvk_1 and extracted_images/mvk_2
folders = [f.path for f in os.scandir('extracted_images/mvk_1') if f.is_dir()] + [f.path for f in os.scandir('extracted_images/mvk_2') if f.is_dir()]

image_paths = []
embeddings = []

# For each folder, get the image paths and embeddings
for folder in folders:
    image_paths.extend([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.jpg')])

    # CLIPFeatures.csv contains the CLIP embeddings for each image (one line per image, each line containing float values separated by ';')
    # put them in embeddings variable (np.array)

    with open(os.path.join(folder, 'CLIPFeatures.csv'), 'r') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            embeddings.append(list(map(float, row)))

embeddings = np.array(embeddings)

# Use KMeans to find 3 representative embeddings
#num_representatives = 3
#kmeans = KMeans(n_clusters=num_representatives, random_state=42).fit(embeddings)
#representative_embeddings = kmeans.cluster_centers_

# Perform hierarchical clustering (using the 'ward' method)
Z = linkage(embeddings, method='ward')

# Cut the dendrogram to get only 'num_representatives' clusters
num_representatives = 35
labels = fcluster(Z, num_representatives, criterion='maxclust')

# For each cluster, compute the centroid (mean of points in the cluster)
representative_embeddings = []
for i in range(1, num_representatives + 1):
    cluster_points = embeddings[labels == i]
    cluster_centroid = cluster_points.mean(axis=0)
    representative_embeddings.append(cluster_centroid)

representative_embeddings = np.array(representative_embeddings)

# Find 1 most similar images for each representative image
num_similar_images = 200
picked_images = []
picked_embeddings = []
for repres_emb in representative_embeddings:
    # Cosine similarity: (A . B) / (||A|| * ||B||)
    similarities = np.dot(embeddings, repres_emb) / (np.linalg.norm(embeddings, axis=1) * np.linalg.norm(repres_emb))
    most_similar_indices = np.argsort(similarities)[-num_similar_images:][::-1]     # Reverse the order to get the most similar images (descending order)
    picked_images.append([image_paths[i] for i in most_similar_indices])
    picked_embeddings.append([embeddings[i] for i in most_similar_indices])

# Print the representative images and their most similar images
attentionChecks = 0 # Skip folder number to make space for attention check folders
for i, rep_images in enumerate(picked_images):
    os.makedirs(f"new_datasets/{(i + 1 + attentionChecks):02}", exist_ok=True)
    print(f"Representative image {i + 1}: {rep_images[0]}")
    print("Copying most similar images")
    for j in range(len(rep_images)):
        img = rep_images[j]
        #print(img)
        # Replace first part of name with j padded to 4 digits
        old_image_name_parts = os.path.basename(img).split('_')
        new_image_name = f"{j:04}_{old_image_name_parts[1]}_{old_image_name_parts[2]}"

        # Save images to new_datasets folder to folder with i + 1 name (padded to 2 digits)
        shutil.copy(img, f"new_datasets/{(i + 1 + attentionChecks):02}/{new_image_name}")

    # Also save the embeddings to a CSV file - CLIPFeatures.csv
    np.savetxt(f"new_datasets/{(i + 1 + attentionChecks):02}/CLIPFeatures.csv", np.array(picked_embeddings[i]), delimiter=';', fmt='%.8e')
        
    print()

    if ((i + 1) % (math.ceil(num_representatives / 3)) == 0):  # Make space always for 2 attention checks
        attentionChecks += 1