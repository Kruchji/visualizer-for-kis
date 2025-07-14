import cv2
import os
import random
from pathlib import Path

def extract_frames_from_videos(source_folder):
    source_folder = Path(source_folder)
    if not source_folder.is_dir():
        raise ValueError(f"Provided path {source_folder} is not a valid folder.")
    
    # Create folder named the same in the extracted:images folder
    output_base = Path("extracted_images") / source_folder.name
    output_base.mkdir(parents=True, exist_ok=True)

    # Get all video files in the folder
    video_files = [f for f in source_folder.iterdir() if f.is_file() and f.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']]
    
    for video_index, video_file in enumerate(video_files, start=0):
        print(f"Processing {video_file.name}...")

        # Create output folder for the video frames
        video_output_folder = output_base / video_file.stem
        video_output_folder.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(str(video_file))
        if not cap.isOpened():
            print(f"Failed to open video file: {video_file}")
            continue

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_idx = 0
        extracted_count = 0

        # Go through all frames in the video
        while frame_idx < total_frames:
            skip = random.randint(15, 60) # Randomly pick frame each 15 to 60 frames
            frame_idx += skip
            if frame_idx >= total_frames:
                break
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                continue

            # Save the frame as an image
            filename = f"{extracted_count:04}_{frame_idx:04}_{video_index:04}.jpg"
            filepath = video_output_folder / filename
            cv2.imwrite(str(filepath), frame)
            extracted_count += 1

        cap.release()
    print("Done.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: extract_images_from_videos.py <path_to_video_folder>")
        sys.exit(1)

    input_folder = sys.argv[1]
    extract_frames_from_videos(input_folder)
