#!/usr/bin/env python3

import h5py
import numpy as np
from PIL import Image
import io, os

main_folder = 'mvk_eye_tracking/'

skipped = 0

currentDatasetID = -1

for folder in ['mvk_1/', 'mvk_2/']: # Use both sources
    # Get subfolders
    file_path = main_folder + folder + 'images.hdf5'
    subfolders = [os.path.basename(f.path) for f in os.scandir(main_folder + folder) if f.is_dir()]

    # For each subfolder, extract the images
    for subfolder in subfolders:
        print(f"Processing {subfolder}...")

        file_path = main_folder + folder + subfolder + '/images.hdf5'

        if not os.path.isfile(file_path):
            print(f"File '{file_path}' not found.")
            skipped += 1
            continue

        keyframes_path = main_folder + folder + subfolder + '/keyframes.txt'

        if not os.path.isfile(keyframes_path):
            print(f"File '{keyframes_path}' not found.")
            skipped += 1
            continue

        clip_path = main_folder + folder + subfolder + '/clip.npy'

        if not os.path.isfile(clip_path):
            print(f"File '{clip_path}' not found.")
            skipped += 1
            continue

        os.makedirs("extracted_images/" + folder + "/" + subfolder, exist_ok=True)

        image_path = os.path.join("extracted_images", folder, subfolder)

        # Open the HDF5 file
        with h5py.File(file_path, 'r') as hdf_file:
            
            # Print all groups and datasets inside the file
            def print_structure(name, obj):
                print(f"{name}: {type(obj)}")

            print("Structure of the HDF5 file:")
            hdf_file.visititems(print_structure)

            dataset_name = 'selected_frames'
            if dataset_name in hdf_file:
                data = hdf_file[dataset_name][:]
                print(f"\nContents of '{dataset_name}':")
                print(data)
            else:
                print(f"\nDataset '{dataset_name}' not found in the file.")

            frames = hdf_file['selected_frames'][:]

            # keyframes.txt file on each line contains number that should be added to image name
            with open(main_folder + folder + subfolder + '/keyframes.txt') as f:
                keyframes = f.readlines()
                keyframes = [int(x.strip()) for x in keyframes]

            # Get dataset id -> last part of subfolder name (separated by '_')
            currentDatasetID += 1

            for i, frame_bytes in enumerate(frames):
                # Convert the byte array to an image
                image = Image.open(io.BytesIO(np.array(frame_bytes)))

                # Save the image to disk
                image.save(f"{image_path}/{i:04}_{keyframes[i]:04}_{currentDatasetID:04}.jpg")
                print(f"Saved {image_path}/{i:04}_{keyframes[i]:04}_{currentDatasetID:04}.jpg")

        # Load the .npy file
        clip_data = np.load(clip_path)

        print("Loaded clip data:", clip_data)

        output_file = "CLIPFeatures.csv"

        np.savetxt(image_path + "/" + output_file, clip_data, delimiter=';', fmt='%.8e')

print(f"Skipped {skipped} folders.")