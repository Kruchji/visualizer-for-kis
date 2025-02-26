#!/usr/bin/env python3

# Model source: https://github.com/Visual-Computing/MCIP

import open_clip
import torch

device = 'cuda' if torch.cuda.is_available() else 'cpu'  # Use GPU if available (else CPU)

model, _, preprocess = open_clip.create_model_and_transforms(
    'ViT-SO400M-14-SigLIP-384',
    pretrained="webli",
    device=device)
checkpoint_path = 'MCIP-ViT-SO400M-14-SigLIP-384.pth'
mcip_state_dict = torch.load(checkpoint_path, map_location=torch.device('cpu'))
model.load_state_dict(mcip_state_dict, strict=True)

tokenizer = open_clip.get_tokenizer('ViT-SO400M-14-SigLIP-384')

def get_text_embedding(text):
    # Tokenize the text
    text_tokens = tokenizer(text).to(device)
    
    # Get text embedding
    with torch.no_grad():
        embedding = model.encode_text(text_tokens).cpu().numpy().flatten()
    
    return embedding

imageDescriptions = [
    "Coral reef",
    "Fish",
    "Human"
]

# Get CLIP features for each image description
clip_features = []
for i, description in enumerate(imageDescriptions):
    embedding = get_text_embedding(description)
    print(f"Embedding for image description {i + 1}: {embedding}")
    clip_features.append(';'.join(map(str, embedding)))

# Save CLIP features to CSV
csv_path = 'CLIPTextFeatures.csv'
with open(csv_path, 'w') as f:
    for feature in clip_features:
        f.write(feature + '\n')