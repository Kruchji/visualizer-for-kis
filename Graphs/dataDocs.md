# Collected Data Documentation
Each user has its own numbered folder. User data is split across 4 files:
- `userConfig.csv`: Extra file. Contains permuted config for this user - datasets, orderings and columns.
- `userData.json`: Stores all general data for user about all iterations.
- `submissions.txt`: Stores all types of submissions (submit, compare, skip,...) made by this user.
- `scrollPositions.txt`: Stores all tracked scroll positions for this user.

## userConfig.csv
File contains 3 columns, separated by semicolon, in this order:
- `dataset`: Name of dataset.
- `ordering`: Ordering of images.
- `columns`: Number of columns in dataset.

## userData.json
Main key in the JSON is the user ID. Then it contains the following keys:
- `lastCompleted`: Last completed iteration (starts at -1).
- `prolificPID`: Prolific ID of the user.
- `studyID`: Prolific study ID.
- `sessionID`: Prolific session ID.
- `reloads`: Number of reloads of the page for each iteration.
- `totalIncorrect`: Total number of incorrect submissions (over all iterations).
- `imagePos`: Position of all images for each iteration.
- `targets`: Target image for each iteration. If target image was missing from dataset, it starts with folder name `target/`.
- `dataSets`: Dataset for each iteration.
- `orderings`: Ordering for each iteration.
- `imagesPerRow`: Number of images per row (columns) for each iteration.

## submissions.txt
Each line in the file represents one submission. It contains 12 columns, separated by semicolon, in this order:
- `userID`: User ID.
- `iteration`: Iteration number.
- `timestamp`: Timestamp of submission (in milliseconds).
- `currentScroll`: Current scroll position.
- `totalScroll`: Total scroll height of the page.
- `navbarHeight`: Height of the navbar.
- `windowHeight`: Height of the browser window.
- `firstRowStart`: Position of the first row of images.
- `secondRowStart`: Position of the second row of images.
- `imageHeight`: Height of one image.
- `submissionType`: Type of submission (submit, compare, skip, ...).
- `imageName/actionName`: Name of the image or action.

There are these 9 types of submissions:
- `0`: Incorrect submission (click on wrong image).
- `1`: Correct submission (click on correct image).
- `2`: Open compare display (click on compare button on some image).
- `3`: Close compare display.
- `4`: Skip iteration.
- `5`: Open target image overlay.
- `6`: Close target image overlay.
- `7`: Open instructions overlay.
- `8`: Close instructions overlay.

## scrollPositions.txt
Each line in the file represents one scroll position. It contains 13 columns, separated by semicolon, in this order:
- `userID`: User ID.
- `iteration`: Iteration number.
- `timestamp`: Timestamp of scroll position (in milliseconds).
- `currentScroll`: Current scroll position.
- `totalScroll`: Total scroll height of the page.
- `windowWidth`: Width of the browser window.
- `windowHeight`: Height of the browser window.
- `navbarHeight`: Height of the navbar.
- `firstRowStart`: Position of the first row of images.
- `secondRowStart`: Position of the second row of images.
- `imageHeight`: Height of one image.
- `missedTarget`: 1 if user scrolled past target image, 0 otherwise.
- `afterLoad`: 1 if this scroll position was first after page load, 0 otherwise. (for tracking reloads)