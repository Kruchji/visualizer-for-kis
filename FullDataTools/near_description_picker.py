#!/usr/bin/env python3

import os, shutil, math
import numpy as np
import csv


# Get folders inside extracted_images/mvk_1 and extracted_images/mvk_2
folders = [f.path for f in os.scandir('extracted_images/mvk_1') if f.is_dir()] + [f.path for f in os.scandir('extracted_images/mvk_2') if f.is_dir()]

image_paths = []
embeddings = []

# For each folder, get the image paths and embeddings
for folder in folders:
    image_paths.extend([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.jpg')])

    # GeneratedCLIPFeatures.csv contains the CLIP embeddings for each image (one line per image, each line containing float values separated by ';')
    # put them in embeddings variable (np.array)

    with open(os.path.join(folder, 'GeneratedCLIPFeatures.csv'), 'r') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            embeddings.append(list(map(float, row)))

embeddings = np.array(embeddings)

# Load the description embeddings from the CSV file descriptionCLIPFeatures.csv
descriptions_embeddings = []
with open('representative_images/descriptionCLIPFeatures.csv', 'r') as f:
    reader = csv.reader(f, delimiter=';')
    for row in reader:
        descriptions_embeddings.append(list(map(float, row)))

number_of_descriptions = len(descriptions_embeddings)

# Also load original representative image target paths (in target_images.txt)
original_representative_images = []
with open('representative_images/target_images.txt', 'r') as f:
    original_representative_images = [os.path.normpath(line.strip()).replace('\\', '/') for line in f] # Remove newline characters and normalize paths

# Find 200 most similar images for each representative description
num_similar_images = 200
picked_images = []
picked_embeddings = []
for descr_emb in descriptions_embeddings:
    # Cosine similarity: (A . B) / (||A|| * ||B||)
    similarities = np.dot(embeddings, descr_emb) / (np.linalg.norm(embeddings, axis=1) * np.linalg.norm(descr_emb))
    most_similar_indices = np.argsort(similarities)[-num_similar_images:][::-1]     # Reverse the order to get the most similar images (descending order)
    picked_images.append([image_paths[i] for i in most_similar_indices])
    picked_embeddings.append([embeddings[i] for i in most_similar_indices])

# Print their most similar images
attentionChecks = 0 # Skip folder number to make space for attention check folders
for i, rep_images in enumerate(picked_images):
    os.makedirs(f"new_datasets/{(i + 1 + attentionChecks):02}", exist_ok=True)
    print(f"Most similar image {i + 1}: {rep_images[0]}")
    print("Copying most similar images")
    targetPicked = False
    for j in range(len(rep_images)):
        img = rep_images[j]
        #print(img)
        # Replace first part of name with j padded to 4 digits
        old_image_name_parts = os.path.basename(img).split('_')
        new_image_name = f"{j:04}_{old_image_name_parts[1]}_{old_image_name_parts[2]}"

        # Save images to new_datasets folder to folder with i + 1 name (padded to 2 digits)
        shutil.copy(img, f"new_datasets/{(i + 1 + attentionChecks):02}/{new_image_name}")

        # if img (path) is equal to the original representative image, save the new name to the chosenTarget.txt file
        if os.path.normpath(img) == os.path.normpath(original_representative_images[i]):
            with open(f"new_datasets/{(i + 1 + attentionChecks):02}/chosenTarget.txt", 'w') as f:
                f.write(new_image_name)
            targetPicked = True

    # If target was not picked, create folder target and save it there (from the path)
    if not targetPicked:
        os.makedirs(f"new_datasets/{(i + 1 + attentionChecks):02}/target", exist_ok=True)
        shutil.copy(original_representative_images[i], f"new_datasets/{(i + 1 + attentionChecks):02}/target")
        # Then in chosenTarget.txt save the target image name
        with open(f"new_datasets/{(i + 1 + attentionChecks):02}/chosenTarget.txt", 'w') as f:
            f.write(f"target/{os.path.basename(original_representative_images[i])}")
            

    # Also save the embeddings to a CSV file - CLIPFeatures.csv
    np.savetxt(f"new_datasets/{(i + 1 + attentionChecks):02}/CLIPFeatures.csv", np.array(picked_embeddings[i]), delimiter=';', fmt='%.8e')

        
    print()

    if ((i + 1) % (math.ceil(number_of_descriptions / 3)) == 0):  # Make space always for 2 attention checks
        attentionChecks += 1