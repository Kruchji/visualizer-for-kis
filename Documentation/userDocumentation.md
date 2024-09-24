## User documentation

The sections below document the functionality of each part of the application.

### First setup

Running the application requires Python 3.10 with pip. Required dependencies can be then installed with `pip install -r requirements.txt`.

### Config

To configure this application, use the CSV file `config.txt`.

With each line you will define board configuration and ordering. These configurations will cyclically repeat on all datasets.

Each line consists of two values:
1) Number of images per row (usually 4 or 8)
2) Desired ordering

Possible ordering values:
- `d` : default folder ordering
- `mc` : middle column first (otherwise same as `d`)
- `ss` : self-sorting
- `r` : random

Configurations are shifted for each user to test all datasets for each configuration equally.

### Datasets

For each dataset of images, put them inside a folder in `Data`. The dataset folder should also contain `CLIPFeatures.csv` which should for each image contain a line with its CLIP features.

### Target generation

Last step of setup is picking a target for each dataset. This is done only once, so that each dataset has fixed target for all board configurations and users. Image is more likely to be picked as a target the closer it is to the first image in the default ordering.

To generate targets for each dataset, run `targetsGenerator.py`. This will create a file `chosenTarget.txt` in each dataset folder with the selected target.

### Running the application

To launch the application, run the file `server.py`. This will start a web server on the port `8001` (accessible at `http://localhost:8001/`).

On this website users can complete specified image search tasks.

### Ordering visualizer controls

The test is started by clicking `Begin the test` button. After all images load, the target image will be displayed and can be dismissed by clicking anywhere. The scrollbar data collection will begin after this overlay is closed.

Users can toggle the target image, toggle fullscreen mode and track their progress using the navigation bar. Each image in the grid can be compared with the target image using the `Compare` button. Users can then submit the image using the `Submit` button which will either show an error message or launch the next iteration of images.

After all datasets are completed, the test will end. A new test can be started using the `Start over / New user` button.

### Generating graphs

After collection some user data, it's possible to generate graphs of each user's search path.

To generate graphs just run `Graphs/graphGenerator.py`. It takes 2 or 3 numerical arguments:
1) User ID
2) Iteration
3) Save the result to an image file (1 = True) (Optional)