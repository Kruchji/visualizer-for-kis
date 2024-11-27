#!/usr/bin/env python3

# Model source: https://github.com/Visual-Computing/MCIP

import open_clip
import torch
from PIL import Image
import os
import numpy as np
#from torchvision.transforms import Compose

device = 'cuda' if torch.cuda.is_available() else 'cpu' # Use GPU if available (else CPU)

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
embeddings = []
for img_path in image_paths:
    embeddings.append(get_image_embedding(img_path))

# Pairwise cosine similarities
embeddings = np.array(embeddings)
num_images = len(embeddings)
similarities = np.zeros((num_images, num_images))

for i in range(num_images):
    for j in range(i + 1, num_images):
        # Cosine similarity: (A . B) / (||A|| * ||B||)
        similarity = np.dot(embeddings[i], embeddings[j]) / (
            np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
        )
        similarities[i, j] = similarity
        similarities[j, i] = similarity

# Find the two most similar images
most_similar_pair = np.unravel_index(np.argmax(similarities, axis=None), similarities.shape)
most_similar_images = (image_paths[most_similar_pair[0]], image_paths[most_similar_pair[1]])

print("The two most similar images are:")
print(most_similar_images)