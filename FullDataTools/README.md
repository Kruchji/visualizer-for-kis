### Instructions to generate datasets

For dataset generation, many images are needed. You can provide these manually in the `extracted_images` folder, or you can use one of the options below. To run these scripts, you may need to install additional dependencies listed in the `requirements.txt` file.

To extract images (frames) from folder with videos:
1) Run [extract_images_from_videos.py](./extract_images_from_videos.py) to extract images from videos from a folder that is supplied as the first argument. It will create a folder `extracted_images` with all extracted images.

If you are using the `mvk_eye_tracking` dataset:
1) Move `mvk_eye_tracking` folder here.
1) Run [extract_images_and_clip.py](./extract_images_and_clip.py) to extract the images (with features) into `extracted_images` folder.

With the extracted images, you can now create datasets:
1) Run [generate_image_features.py](./generate_image_features.py) to generate new local features for all images in the `extracted_images` folder (also make sure to download the CLIP model checkpoint into the [../CLIP](../CLIP) folder).
1) Run [only_representative_picker.py](./only_representative_picker.py) to generate representative images (into `representative_images` folder). 
1) For each representative image write a text description on one line in the file `descriptions.txt` inside `representative_images`.
1) Run [localCLIPDescriptionsFeaturesGenerator.py](./localCLIPDescriptionsFeaturesGenerator.py) to get features for all text descriptions.
1) Next run [near_description_picker.py](./near_description_picker.py) to create datasets with images nearest to descriptions (in `new_datasets` folder) and the `chosenTarget.txt` files.
1) Finally you should run [lab_feature_extractor.py](./lab_feature_extractor.py) to get LAB features for images.
1) Move the datasets (folders) to [../Data](../Data) folder.
