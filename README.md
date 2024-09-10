## Ordering Visualizer for Known-item search

### Setup instructions

1) Install dependencies with `pip install -r requirements.txt`.
2) Generate targets for each dataset by running `targetsGenerator.py`.
3) Edit `config.txt` to desired layout and sorting of images.
4) Run `server.py`.
5) Have users open `http://localhost:8001/` and complete image search tasks.
6) To then generate a graph for a specific user (first argument) and iteration (second argument) run `Graphs/graphGenerator.py`. Set third argument to `1` to save the result to a file.