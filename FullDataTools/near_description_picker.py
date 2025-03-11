#!/usr/bin/env python3

import os, shutil, math
import numpy as np
import csv

# Extracts frame number and video ID from the image path
def extract_frame_and_video(img):
    parts = os.path.basename(img).split('_')
    return int(parts[1]), parts[2].split('.')[0]  # Frame number, Video ID

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
frame_threshold = 30  # in frames - enforced on both sides
picked_images = []
picked_embeddings = []
for i, descr_emb in enumerate(descriptions_embeddings):
    # Cosine similarity: (A . B) / (||A|| * ||B||)
    similarities = np.dot(embeddings, descr_emb) / (np.linalg.norm(embeddings, axis=1) * np.linalg.norm(descr_emb))
    most_similar_indices = np.argsort(similarities)[-num_similar_images*3:][::-1]     # Reverse the order to get the most similar images (descending order) (plus take more to account for conflicts)

    selected_images = []
    selected_embeddings = []
    seen_frames = {}  # Track seen frames per video

    confl_counter = 0

    # Loop until enough valid images are picked
    for idx in most_similar_indices:
        # Get image and its values
        img_path = image_paths[idx]
        frame_num, video_id = extract_frame_and_video(img_path)

        # Check if the current image is the original representative
        if os.path.normpath(img_path) == os.path.normpath(original_representative_images[i]):
            # Force-include the representative image and remove conflicting ones
            selected_images = [img for img in selected_images if extract_frame_and_video(img)[1] != video_id or abs(extract_frame_and_video(img)[0] - frame_num) > frame_threshold]
            selected_embeddings = [embeddings[image_paths.index(img)] for img in selected_images]
            selected_images.append(img_path)
            selected_embeddings.append(embeddings[idx])

            orig_size = len(seen_frames.get(video_id, []))

            # Recompute the seen frames for this video
            seen_frames.setdefault(video_id, [])
            seen_frames[video_id] = [f for f in seen_frames[video_id] if abs(f - frame_num) > frame_threshold]
            seen_frames[video_id].append(frame_num)

            print(f"Force-included target: {img_path}, removed {orig_size - len(seen_frames[video_id]) + 1} conflicting images")
            continue

        # Skip if there's a conflict withing the specified range
        if video_id in seen_frames and any(abs(frame_num - seen_frame) <= frame_threshold for seen_frame in seen_frames[video_id]):
            #print(f"Conflict: {img_path} with {seen_frames[video_id]}")
            confl_counter += 1
            continue

        # Add image if no conflict
        selected_images.append(img_path)
        selected_embeddings.append(embeddings[idx])
        seen_frames.setdefault(video_id, []).append(frame_num)

        # Stop when enough images are picked
        if len(selected_images) == num_similar_images:
            break

    # For each description, save the most similar images and their embeddings
    picked_images.append(selected_images)
    picked_embeddings.append(selected_embeddings)
    print(f"End of description {i + 1}, conflicts: {confl_counter}\n")


# Print their most similar images
attentionChecks = 0 # Skip folder number to make space for attention check folders
missingTargets = 0
targetRanksSum = 0
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

            print(f"Target rank: {j + 1}")
            targetRanksSum += j + 1

    # If target was not picked, create folder target and save it there (from the path)
    if not targetPicked:
        os.makedirs(f"new_datasets/{(i + 1 + attentionChecks):02}/target", exist_ok=True)
        shutil.copy(original_representative_images[i], f"new_datasets/{(i + 1 + attentionChecks):02}/target")
        # Then in chosenTarget.txt save the target image name
        with open(f"new_datasets/{(i + 1 + attentionChecks):02}/chosenTarget.txt", 'w') as f:
            f.write(f"target/{os.path.basename(original_representative_images[i])}")

        print("Saved missing target to: ", f"new_datasets/{(i + 1 + attentionChecks):02}/target/{os.path.basename(original_representative_images[i])}")
        missingTargets += 1

    # Also save the embeddings to a CSV file - CLIPFeatures.csv
    np.savetxt(f"new_datasets/{(i + 1 + attentionChecks):02}/CLIPFeatures.csv", np.array(picked_embeddings[i]), delimiter=';', fmt='%.8e')

        
    print()

    if ((i + 1) % (math.ceil(number_of_descriptions / 3)) == 0):  # Make space always for 2 attention checks
        attentionChecks += 1

print(f"\nTotal missing targets: {missingTargets}")
print(f"Average target rank: {targetRanksSum / (number_of_descriptions - missingTargets):.2f}\n")