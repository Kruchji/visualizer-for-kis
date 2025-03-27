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
mcip_state_dict = torch.load(checkpoint_path, map_location=torch.device('cpu'))
model.load_state_dict(mcip_state_dict, strict=True)
# tokenizer = open_clip.get_tokenizer('ViT-SO400M-14-SigLIP-384')


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

folder_path = 'Images/Features'
    
clip_features = []
for j, img_path in enumerate(image_paths):
    original_name = os.path.basename(img_path)
    new_name = f'{j:04d}__{original_name}'
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