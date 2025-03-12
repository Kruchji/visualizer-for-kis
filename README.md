## Ordering Visualizer for Known-item search

This project creates a testing and data collection environment for known-item search. It allows testing different image board configurations and orderings (specified below). It can also generate graphs based on the collected data.

### Setup instructions

1) Install dependencies with `pip install -r requirements.txt`.
1) Generate datasets using scripts in [FullDataTools](./FullDataTools) folder (see [README](./FullDataTools/README.md) in that folder for more information).
1) Edit [config.txt](./config.txt) to desired layout and ordering of images.
1) Optionally create [attentionCheckIndices.txt](./Data/attentionCheckIndices.txt) file with indices of datasets (one index on each line) that should be used as attention checks. These datasets will not be added to the latin square in the next step and instead will be inserted equally between the other datasets with 4 columns and `sp` ordering.
1) Run [configGenerator.py](./configGenerator.py) to generate a large latin square of configurations for all users. (lower number of configs or datasets to make this step run faster)
1) Run [server.py](./server.py). (Use option `--admin` to enable admin mode.)
1) Have users open `http://localhost:8001/` and complete image search tasks.
1) To then generate a graph for a specific user (first argument) and iteration (second argument) run [Graphs/iterationGraphGenerator.py](./Graphs/iterationGraphGenerator.py). Set third argument to `1` to save the result to a file. To generate a graph for all users that completed a dataset with a specific ordering use [Graphs/datasetGraphGenerator.py](./Graphs/datasetGraphGenerator.py).

### Config

Config file is CSV with the first value being number of images per row (4,8) and the second the desired ordering. Datasets are shifted for each user to test all datasets for each configuration.

Possible ordering values:
- `d` : default folder ordering
- `sp` : side-panel (otherwise same as `d`)
- `mc` : middle column first (otherwise same as `d`)
- `ss` : self-sorting
- `r` : random
- `lab` : LAB color self-sorting
- `group` : group by video