#!/usr/bin/env python3

import os, shutil, math
import numpy as np
import csv
from PIL import Image

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

# Create a directory to save conflicting images
CONFLICTING_IMAGES_DIR = "conflicting_images"
os.makedirs(CONFLICTING_IMAGES_DIR, exist_ok=True)

# Find 200 most similar images for each representative description
num_similar_images = 200
frame_threshold = 25  # in frames - enforced on both sides
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
            # Identify and print conflicting images with their cosine similarity
            interfering_images = []
            for img in selected_images:
                img_frame, img_video_id = extract_frame_and_video(img)
                if img_video_id == video_id and abs(img_frame - frame_num) <= frame_threshold:
                    embIndex = image_paths.index(img)
                    similarity = np.dot(embeddings[embIndex], embeddings[idx]) / (np.linalg.norm(embeddings[embIndex]) * np.linalg.norm(embeddings[idx]))
                    interfering_images.append((img, similarity))

            if interfering_images:
                print(f"Target image: {img_path} has {len(interfering_images)} conflicting images:")
                for img, similarity in interfering_images:
                    print(f"  - {img} (Cosine Similarity: {similarity:.4f})")

                    # Create a side-by-side comparison image
                    target_img = Image.open(img_path)
                    conflicting_img = Image.open(img)

                    # Resize images to have the same height
                    height = max(target_img.height, conflicting_img.height)
                    target_img = target_img.resize((int(target_img.width * (height / target_img.height)), height))
                    conflicting_img = conflicting_img.resize((int(conflicting_img.width * (height / conflicting_img.height)), height))

                    # Create a new image combining both
                    combined_img = Image.new("RGB", (conflicting_img.width + target_img.width, height))
                    combined_img.paste(conflicting_img, (0, 0))
                    combined_img.paste(target_img, (conflicting_img.width, 0))

                    # Save the combined image
                    combined_img_path = os.path.join(CONFLICTING_IMAGES_DIR, f"comparison_{i}_{os.path.basename(img)}")
                    combined_img.save(combined_img_path)

            # Replace the original representative with the most similar conflicting image
            if interfering_images:
                most_similar_image = max(interfering_images, key=lambda x: x[1])[0]
                original_representative_images[i] = most_similar_image
                print(f"Replaced target image with {most_similar_image}\n")
            

        # Skip if there's a conflict withing the specified range
        if video_id in seen_frames and any(abs(frame_num - seen_frame) <= frame_threshold for seen_frame in seen_frames[video_id]):
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
missingTargets = 0
targetRanksSum = 0
for i, rep_images in enumerate(picked_images):
    os.makedirs(f"new_datasets/{(i + 1):02}", exist_ok=True)
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
        shutil.copy(img, f"new_datasets/{(i + 1):02}/{new_image_name}")

        # if img (path) is equal to the original representative image, save the new name to the chosenTarget.txt file
        if os.path.normpath(img) == os.path.normpath(original_representative_images[i]):
            with open(f"new_datasets/{(i + 1):02}/chosenTarget.txt", 'w') as f:
                f.write(new_image_name)
            targetPicked = True

            print(f"Target rank: {j + 1}")
            targetRanksSum += j + 1

    # If target was not picked, create folder target and save it there (from the path)
    if not targetPicked:
        os.makedirs(f"new_datasets/{(i + 1):02}/target", exist_ok=True)
        shutil.copy(original_representative_images[i], f"new_datasets/{(i + 1):02}/target")
        # Then in chosenTarget.txt save the target image name
        with open(f"new_datasets/{(i + 1):02}/chosenTarget.txt", 'w') as f:
            f.write(f"target/{os.path.basename(original_representative_images[i])}")

        print("Saved missing target to: ", f"new_datasets/{(i + 1):02}/target/{os.path.basename(original_representative_images[i])}")
        missingTargets += 1

    # Also save the embeddings to a CSV file - CLIPFeatures.csv
    np.savetxt(f"new_datasets/{(i + 1):02}/CLIPFeatures.csv", np.array(picked_embeddings[i]), delimiter=';', fmt='%.8e')

    print()

print(f"\nTotal missing targets: {missingTargets}")
print(f"Average target rank: {targetRanksSum / (number_of_descriptions - missingTargets):.2f}\n")