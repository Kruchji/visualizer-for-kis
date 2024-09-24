## Programming documentation

The sections below will document each part of the application, configuration and data collection (format).

### Project overview

This project aims to create an environment for known-item search and ordering visualisation with scrollbar data collection.

It consists of many files (and folders), some of which can be grouped together:

- `script.js`, `index.html`, `style.css` (, `favicon.ico`) - Provide frontend website and data collection.
- `server.py`, `selfSort.py` - Provide backend server, store data (collected by frontend) and configurations and generate orderings.
- `targetsGenerator.py` - Generates target for each dataset.
- `config.txt` - Used to specify board configurations.
- `Data` - Contains folders for each dataset that consists of images and CLIP features. They may also contain files with generated targets.
- `CollectedData` - Contains three files with collected data from users (`scrollPositions.txt`, `submissions.txt`) and user configurations (`userData.json`).
- `Graphs`, `Graphs/graphGenerator.py` - Used for graph generation from collected data. May create `graph.png` in this directory.
- `Libs` - Folder containing Bootstrap and jQuery libraries.
- `Documentation` - Project documentation files.

### Requirements

Running the application requires Python 3.10 with pip. Dependencies are included in the file `requirements.txt` - they are numpy, matplotlib, scipy and lap. These are used in ordering calculations and target and graph generation.

### Frontend

### Backend (server)

The backend server is handled by `server.py`. It uses Python's built-in http.server to handle all (POST) requests incoming from frontend on port `8001`. It also imports `selfSort.py` to calculate self-sorted ordering faster than if it was calculated later using JavaScript.

The server always first extracts user ID and iteration number from each query from the URL. This value is provided with each request from the frontend except for user creating and loading (where its values is not used).

The next action is decided using `elif` statements iteration over possible requests: `newUser`, `oldUser`, `getImages`, `imageConfig`, `scrollPositions` and `submissions`.

`newUser` is a request with no data provided from the frontend. It finds the highest stored user ID and increments it to get a new user ID. It then stores it in user configuration and sends the ID along with the total number of datasets (for displaying progress on frontend) back to frontend.

`oldUser` receives the ID of an existing user (stored in local storage on frontend browser) and attempts to load the user's data. If no error is encountered the reloads counter is increased by one and all user board data is sent back to frontend. On error dummy error data is send instead ("END") which ends the test on frontend (but offers option to start a new test with new user).

`getImages` receives no additional data. It gets the next dataset for a user and increments the current iteration (or detect end of a test). It then also loads the configuration for said iteration and user. And it also reads the target image and the CLIP features from the included file and calculates the self-sorted ordering using the code in `selfSort.py` (included with author permission). At last, a response is sent to the frontend with default ordering and self-sorted ordering of image filenames, dataset, target image and configuration data.

The code `selfSort.py` was edited slightly to allow for non-square (rectangular) boards of images.

`imageConfig` receives image positions, target image, dataset, ordering and number of images per row from the frontend. It then stores these values into user configuration file.

`scrollPositions` and `submissions` store all received data from frontend to CSV file. See section `Collected data` to learn which data is received.

### Target generation

To have comparable data between users, the a specific target is used for each dataset, so that all users are attempting to find the same image. To generate these targets, you can use the provided script `targetsGenerator.py` which will create `chosenTarget.txt` for each dataset. You can also provide it yourself; the file only includes filename of one of the images in the dataset.

The script `targetsGenerator.py` doesn't pick the target completely at random. It uses this formula to get weights: $\frac{1}{(imageIndex + 1)^0.4}$ where imageIndex is the number of image in the dataset. This kind of target generation prioritizes images that are near the top in default ordering (which should speed up search).

### Configuration

The board image configurations and orderings are set in `config.txt`. These are used only when generating a new board for a user, thus changing the configuration does not interfere with previously collected data (The configuration is stored as part of the data collection process, described in other sections.).

Each line of the CSV file defines board configuration and ordering. These configurations will cyclically repeat on all datasets.

Each line consists of two values, separated by a comma:
1) Number of images per row (usually 4 or 8)
2) Desired ordering

Possible ordering values:
- `d` : default folder ordering
- `mc` : middle column first
- `ss` : self-sorting
- `r` : random

The middle column first fills first the middle columns with images and then puts the rest on the sides. This ordering option was added because it was observed that people often focus on the middle images first.

Self-sorting ordering is calculated using code in `selfSort.py` (taken with permission from another study).

Configurations are shifted for each user to test all datasets for each configuration equally (`(UserID + currentIteration) % numOfBoardConfigs`).

The default configuration is:

```
4;d
8;mc
8;ss
```

A smaller number of configurations (3) was chosen to have enough data for meaningful comparison even for smaller number of users. All ordering types are represented except random which could be included to serve as a baseline (but was excluded here to keep the number of configurations low).

### Datasets

Datasets to be included should be stored in the `Data` folder, with each dataset having its unique folder. A dataset should include a set of images and a `CLIPFeatures.csv` file with CLIP features of all included images. The file should on each line contain a vector (floats separated by a semicolon) coresponding to each image in dataset. After target generation each dataset folder should also include a `chosenTarget.txt` file with one image filename.

The dataset will be cycled through for each new iteration the user loads. Each new user will also start one configuration ahead of the previous user. This ensures that all board configurations and ordering are tested on all datasets equally. User has as many iterations to complete as there are datasets.

Included example datasets were taken with permission from an Eye tracking study. The focus on sea floor images, many of which are very similar (thus the search takes a bit of time).

### Collected data

All collected data is saved by backend into the `CollectedData` folder into three files: `scrollPositions.txt`, `submissions.txt` and `userData.json`.

`scrollPositions.txt` contains 12 columns separated by semicolons which correspond to:
1) User ID
2) Iteration number
3) Timestamp
4) Scroll height from the top of the page
5) Total scroll height of the page
6) Window width
7) Window height
8) Navigation bar height
9) Start (height) of first row
10) Start (height) of second row
11) Image height (in the grid)
12) Boolean if target was already missed (was on screen but user scrolled past it)

The different heights are collected to precisely calculate the user movement even when window size changes. Starting location of first and second row can be used to calculate the location of every image in the board.

`submissions.txt` also contains 12 columns (separated by semicolons) that correspond to:
1) User ID
2) Iteration number
3) Timestamp
4) Scroll height from the top of the page
5) Total scroll height of the page
6) Navigation bar height
7) Window height
8) Start (height) of first row
9) Start (height) of second row
10) Image height (in the grid)
11) Interaction ID
12) Clicked image filename

First added is clicked image filename to precisely identify the image in a row of images. Second is interaction ID - its value can be:
 - `0` - Incorrect image submission
 - `1` - Correct image submission
 - `2` - Start of compare (compare button clicked)
 - `3` - End of compare (compare overlay closed)

`userData.json` is a JSON file with a specific structure to store all data for each user. For each user ID it contains a JSON with values, each of which (except `lastCompleted`) can be indexed by iteration number:
 - `lastCompleted` - Stores progress of the user through the test. Used when loading existing user.
 - `reloads` - Stores number of reloads for each iteration.
 - `imagePos` - Stores configurations of images as list of filenames for each iteration.
 - `targets` - Stores each iteration's target image filename.
 - `dataSets` - Stores dataset name for each iteration.
 - `orderings` - Stores ordering name for each iteration.
 - `imagesPerRow` - Stores number of images on a row for each iteration.

 This data can be used to completely restore user's board for each iteration if necessary (loading existing user) or when analyzing the data.

### Graphs

Graphs can be generated using the provided script `Graphs/graphGenerator.py`. It takes 2 or 3 numerical arguments:
1) User ID
2) Iteration
3) Save the result to an image file (1 = True) (Optional)

The script then reads all three files from `CollectedData` to extract data needed for specified user and iteration. First from `userData.json` it gets the ordering of images, target image, ordering, dataset and images per row. Then matching `scrollPositions.txt` entries are added to graph plot (as a range), with calculated target position (from the height difference between image rows).

A function `normaliseHeight(currHeight, totalHeight)` is used here to convert all heights to percentage relative to the total page size. It also inverts the percentage (by subtracting it from a 100) so that it represents percentage scrolled.

Next, reloads are marked in the graph as lines. They are detected from long times between data entries (>1.5s).

Finally, submissions (interactions) are loaded from `submissions.txt` and plotted. Colors and style depend on the type of interaction (correct and incorrect submission, compare) as specified above in Collected data section.

At the end the rest of the labels and titles for the graph are specified and the graph is plotted either on screen or into a file `graph.png`, per used arguments.

### Libraries

This project uses two external libraries - Bootstrap and jQuery. Both are already included in the `Libs` folder.