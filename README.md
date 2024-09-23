## Ordering Visualizer for Known-item search

This project creates a testing and data collection environment for known-item search. It allows testing different image board configurations and orderings (specified below). It can also generate graphs based on the collected data.

### Setup instructions

1) Install dependencies with `pip install -r requirements.txt`.
2) Generate targets for each dataset by running `targetsGenerator.py`.
3) Edit `config.txt` to desired layout and ordering of images.
4) Run `server.py`.
5) Have users open `http://localhost:8001/` and complete image search tasks.
6) To then generate a graph for a specific user (first argument) and iteration (second argument) run `Graphs/graphGenerator.py`. Set third argument to `1` to save the result to a file.

### Config

Config file is CSV with the first value being number of images per row (4,8) and the second the desired ordering. Datasets are shifted for each user to test all datasets for each configuration.

Possible ordering values:
- `d` : default folder ordering
- `mc` : middle column first (otherwise same as `d`)
- `ss` : self-sorting
- `r` : random