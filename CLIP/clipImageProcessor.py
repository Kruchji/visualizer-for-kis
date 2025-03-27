#!/usr/bin/env python3

# Model source: https://github.com/Visual-Computing/MCIP

import open_clip
import torch
from PIL import Image
import os
import numpy as np
from sklearn.cluster import KMeans
import shutil
#from torchvision.transforms import Compose

device = 'cuda' if torch.cuda.is_available() else 'cpu'  # Use GPU if available (else CPU)

model, _, preprocess = open_clip.create_model_and_transforms(
    'ViT-SO400M-14-SigLIP-384',
    pretrained="webli",
    device=device)
checkpoint_path = 'MCIP-ViT-SO400M-14-SigLIP-384.pth'
mcip_state_dict = torch.load(checkpoint_path)
model.load_state_dict(mcip_state_dict, strict=True)
tokenizer = open_clip.get_tokenizer('ViT-SO400M-14-SigLIP-384')


# Computes image embeddings
def get_image_embedding(image_path):
    image = Image.open(image_path).convert("RGB")
    image_tensor = preprocess(image).unsqueeze(0).to(device)  # Preprocess

    with torch.no_grad():
        embedding = model.encode_image(image_tensor).cpu().numpy().flatten()  # Get embedding

    return embedding

# Load all images and compute embeddings
image_folder = 'Images'
image_paths = [os.path.join(image_folder, f) for f in os.listdir(image_folder) if f.endswith('.jpg')]
image_paths.sort()
embeddings = []
for img_path in image_paths:
    embeddings.append(get_image_embedding(img_path))

# Convert embeddings to numpy array
embeddings = np.array(embeddings)

# Use KMeans to find 30 representative images
num_representatives = 30
kmeans = KMeans(n_clusters=num_representatives, random_state=42).fit(embeddings)
representative_indices = kmeans.cluster_centers_.argsort(axis=0)[:num_representatives]

# Find 200 most similar images for each representative image
num_similar_images = 200
representative_images = []
for idx in representative_indices:
    # Cosine similarity: (A . B) / (||A|| * ||B||)
    similarities = np.dot(embeddings, embeddings[idx]) / (np.linalg.norm(embeddings, axis=1) * np.linalg.norm(embeddings[idx]))
    most_similar_indices = np.argsort(similarities)[-num_similar_images:]
    representative_images.append([image_paths[i] for i in most_similar_indices])

# Print the representative images and their most similar images
for i, rep_images in enumerate(representative_images):
    print(f"Representative image {i + 1}: {rep_images[0]}")
    print("Most similar images:")
    for img in rep_images:
        print(img)
    print()

# Create Data folder if it doesn't exist
data_folder = 'Data'
if not os.path.exists(data_folder):
    os.makedirs(data_folder)

# Save images and CLIP features
for i, rep_images in enumerate(representative_images):
    folder_path = os.path.join(data_folder, f'{i+1}')
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    clip_features = []
    for j, img_path in enumerate(rep_images):
        original_name = os.path.basename(img_path)
        new_name = f'{j:04d}_{original_name}'
        new_path = os.path.join(folder_path, new_name)
        shutil.copy(img_path, new_path)
        
        # Get the embedding for the image
        embedding = get_image_embedding(img_path)
        clip_features.append(';'.join(map(str, embedding)))
    
    # Save CLIP features to CSV
    csv_path = os.path.join(folder_path, 'CLIPFeatures.csv')
    with open(csv_path, 'w') as f:
        for feature in clip_features:
            f.write(feature + '\n')