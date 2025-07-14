#!/usr/bin/env python3

# Model source: https://github.com/Visual-Computing/MCIP

import open_clip
import torch    # Install for gpu: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
from PIL import Image
import os

# Use GPU if available (else CPU)
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# Define the model
model, _, preprocess = open_clip.create_model_and_transforms(
    'ViT-SO400M-14-SigLIP-384',
    pretrained="webli",
    device=device)
checkpoint_path = '../CLIP/MCIP-ViT-SO400M-14-SigLIP-384.pth'
mcip_state_dict = torch.load(checkpoint_path)
model.load_state_dict(mcip_state_dict, strict=True)
# tokenizer = open_clip.get_tokenizer('ViT-SO400M-14-SigLIP-384')


# Computes image embeddings
def get_image_embedding(image_path):
    image = Image.open(image_path).convert("RGB")
    image_tensor = preprocess(image).unsqueeze(0).to(device)  # Preprocess

    with torch.no_grad():
        embedding = model.encode_image(image_tensor).cpu().numpy().flatten()  # Get embedding

    return embedding


base_folder = 'extracted_images'
subfolders = [f.name for f in os.scandir(base_folder) if f.is_dir()]

# Loop over all subfolders
for subfolder in subfolders:
    subfolder_path = os.path.join(base_folder, subfolder)

    # Loop through each folder inside
    for folder_name in os.listdir(subfolder_path):
        folder_path = os.path.join(subfolder_path, folder_name)

        # Process directories
        if os.path.isdir(folder_path):

            # Load all images and compute embeddings
            image_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.jpg')]
            image_paths.sort()
            
            clip_features = []
            for img_path in image_paths:
                # Get the embedding for the image
                embedding = get_image_embedding(img_path)
                clip_features.append(';'.join(map(str, embedding)))

            # Save CLIP features to CSV
            csv_path = os.path.join(folder_path, 'GeneratedCLIPFeatures.csv')
            with open(csv_path, 'w') as f:
                for feature in clip_features:
                    f.write(feature + '\n')

            print(f'Features saved for folder: {folder_path}')