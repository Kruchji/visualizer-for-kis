#!/usr/bin/env python3

import csv, os, json

# Define the input and output files
OUTPUT_CSV = "dataOverview.csv"
BASE_DIR = "../CollectedData"

# Define the columns for the CSV file
CSV_COLUMNS = [
    "userPID", "userID", "taskOrder", "collectionID", "displayType", "columns",
    "correctImageSubmissions", "totalImagesubmissions", "skipClick", "wasTargetInList",
    "comparisons", "targetAdditionallyDisplayed", "instructionsDisplayed", "missedTargetImage",
     "timeDuration"
]

# Initialize the CSV file with headers
with open(OUTPUT_CSV, mode="w", newline="") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
    writer.writeheader()

# Iterate over all user data folders
for user_dir in os.listdir(BASE_DIR):
    if not os.path.isdir(os.path.join(BASE_DIR, user_dir)):
        continue    # Skip files (non-folders)

    user_id = int(user_dir)
    user_path = os.path.join(BASE_DIR, user_dir)

    # Load userData.json
    try:
        with open(os.path.join(user_path, "userData.json"), "r") as json_file:
            user_data = json.load(json_file)
    except FileNotFoundError:
        print(f"User data not found for user {user_id}. Skipping...")
        continue

    user_pid = user_data[str(user_id)]["prolificPID"]

    # Go over all iterations for the user
    for iteration in range(len(user_data[str(user_id)]["targets"])):

        # Extract data from userData.json
        display_type = user_data[str(user_id)]["orderings"][str(iteration)]
        collection_id = user_data[str(user_id)]["dataSets"][str(iteration)]
        columns = user_data[str(user_id)]["imagesPerRow"][str(iteration)]

        # Check if the target was not in the list (target image entry starts with "target" folder)
        was_in_list = 1
        if user_data[str(user_id)]["targets"][str(iteration)].startswith("target"):
            was_in_list = 0

        # Initialize counters / bools
        correct_submissions = 0
        total_submissions = 0
        skip_submission = 0
        comparisons = 0
        time_duration = 0
        target_overlay_opens = 0
        instructions_displayed = 0

        # Process submissions data
        try:
            with open(os.path.join(user_path, "submissions.txt"), "r") as submissions_file:
                reader = csv.reader(submissions_file, delimiter=";")
                for row in reader:
                    if int(row[0]) == user_id and int(row[1]) == iteration:
                        
                        sub_correct = int(row[10])

                        if sub_correct == 0:  # Incorrect
                            total_submissions += 1
                        elif sub_correct == 1:  # Correct
                            correct_submissions += 1
                            total_submissions += 1

                        elif sub_correct == 2:  # Compare
                            comparisons += 1

                        elif sub_correct == 4:  # Skip click
                            skip_submission += 1

                        elif sub_correct == 5: # Display target overlay
                            target_overlay_opens += 1

                        elif sub_correct == 7: # Display instructions
                            instructions_displayed += 1

        except FileNotFoundError:
            print(f"Submissions file not found for user {user_id}, iteration {iteration}. Skipping...")

        missed_image = 0    # If user missed the target image (scrolled past it)

        # Process scroll positions data
        try:
            with open(os.path.join(user_path, "scrollPositions.txt"), "r") as scroll_file:
                reader = csv.reader(scroll_file, delimiter=";")

                # Get all scroll timestamps for the current user and iteration
                timestamps = []

                for row in reader:
                    if int(row[0]) == user_id and int(row[1]) == iteration:
                        timestamps.append(int(row[2]))

                        # Check if user missed the target image
                        if int(row[11]) == 1:
                            missed_image = 1

                if timestamps:
                    # Calculate the time taken for the task
                    time_duration = (max(timestamps) - min(timestamps)) / 1000  # Convert to seconds

        except FileNotFoundError:
            print(f"Scroll positions file not found for user {user_id}, iteration {iteration}. Skipping...")

        # Write the data row to the final CSV file
        with open(OUTPUT_CSV, mode="a", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
            writer.writerow({
                "userPID": user_pid,
                "userID": user_id,
                "taskOrder": iteration,
                "collectionID": collection_id,
                "displayType": display_type,
                "columns": columns,
                "correctImageSubmissions": correct_submissions,
                "totalImagesubmissions": total_submissions,
                "skipClick": skip_submission,
                "wasTargetInList": was_in_list,
                "comparisons": comparisons,
                "targetAdditionallyDisplayed": target_overlay_opens,
                "instructionsDisplayed": instructions_displayed,
                "missedTargetImage": missed_image,
                "timeDuration": time_duration
            })

    print(f"User {user_pid} ({user_id}) data processed.")

print(f"Data overview CSV file created: {OUTPUT_CSV}")