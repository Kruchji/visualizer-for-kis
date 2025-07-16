
from constraint import Problem, AllDifferentConstraint
import random, math, os, csv, sys
import time
import numpy as np

# Get number of users from command line arguments
if len(sys.argv) >= 2:
    users = int(sys.argv[1])
else:
    users = 126

# Use constraint library to generate a random Latin square
def generate_random_latin_square(values, configSize, numOfDatasets, numOfUsers=126):
    n = len(values)
    collected_latin_square_solutions = []

    # Generate each latin square with differently (randomly) shuffled domains / values
    while len(collected_latin_square_solutions) < ((math.ceil(numOfUsers / configSize)) * (math.ceil(numOfDatasets / configSize))): # (number of users * number of datasets) / config size = 90 (default)
        problem = Problem()

        # Variable for each cell in the Latin square
        for row in range(n):
            for col in range(n):
                domain = values[:]
                random.shuffle(domain)
                problem.addVariable((row, col), domain)
        
        # All rows must be unique
        for row in range(n):
            problem.addConstraint(AllDifferentConstraint(), [(row, col) for col in range(n)])
        
        # All columns must be unique
        for col in range(n):
            problem.addConstraint(AllDifferentConstraint(), [(row, col) for row in range(n)])
        
        # Get one solution
        latin_solution = problem.getSolution()
        if not latin_solution:
            raise ValueError("No Latin square possible with the given values.")
        
        collected_latin_square_solutions.append(latin_solution)
    
    # Convert solution dictionaries back to 2D array (numpy) and store them in a list
    latin_squares = []
    for random_solution in collected_latin_square_solutions:
        latin_square = np.zeros((n, n), dtype=object)
        for key, value in random_solution.items():
            latin_square[key[0], key[1]] = value
        latin_squares.append(latin_square)
    
    return latin_squares

# Get base board configurations
baseConfigData = []
with open("config.txt", "r") as configFile:
    reader = csv.reader(configFile, delimiter=';')
    for row in reader:
        baseConfigData.append({"ord": row[1], "size": int(row[0])})
baseConfigLength = len(baseConfigData)

# Get dataset (images) folders
datasetFolders = [folder for folder in os.listdir("./Data/") if os.path.isdir(f"./Data/{folder}")]
datasetFolders.sort(key=int)

# Get attention check indexes
attentionCheckIndexes = []

# First check if the file exists
if os.path.isfile("./Data/attentionCheckIndices.txt"):
    # On each line of attentionChecks.txt is an index of a dataset folder that should be an attention check
    with open("./Data/attentionCheckIndices.txt", "r") as attentionCheckFile:
        for line in attentionCheckFile:
            datasetIndex = int(line.strip())
            # Check if not out of bounds
            if datasetIndex < len(datasetFolders):
                if datasetIndex not in attentionCheckIndexes:
                    attentionCheckIndexes.append(datasetIndex)
                else:
                    print(f"Attention check index {datasetIndex} is already in the list.")
            else:
                print(f"Attention check index {datasetIndex} is out of bounds.")


# Get number of not attention check datasets
numberOfRealDatasets = len(datasetFolders) - len(attentionCheckIndexes)
numberOfRepeatConfigs = math.ceil((numberOfRealDatasets) / baseConfigLength)    # Generate enough to cover all datasets

# Make base configs unique
uniqueConfigs = []
for i, baseConfig in enumerate(baseConfigData):
    uniqueConfigs.append((baseConfig['size'], baseConfig['ord'], i))  # Add index to make entries unique

# Generate Latin squares
startTime = time.time()
generatedLatinSquareList = generate_random_latin_square(uniqueConfigs, baseConfigLength, numberOfRealDatasets, numOfUsers=users)
print(f"Time taken to generate {((math.ceil(users / baseConfigLength)) * (math.ceil(numberOfRealDatasets / baseConfigLength)))} Latin squares: {time.time() - startTime} seconds")

# Combine smaller latin squares into one large one
latinSquareGrid = np.array(generatedLatinSquareList).reshape(math.ceil(users / baseConfigLength), math.ceil(numberOfRealDatasets / baseConfigLength), baseConfigLength, baseConfigLength)
largeLatinSquareRows = [np.hstack(row) for row in latinSquareGrid]
largeGeneratedLatinSquare = np.vstack(largeLatinSquareRows)

# Store the Latin square differently and remove the last element (index)
latinSquareConfigs = []
for i in range(len(largeGeneratedLatinSquare)):
    latinSquareConfigs.append([])

    for j in range(len(largeGeneratedLatinSquare[i])):
        # Split the tuple, remove the last element (index), and extract the size and ord
        size, ord, _ = largeGeneratedLatinSquare[i][j]  # _ => ignore the last element

        latinSquareConfigs[i].append({"ord": ord, "size": int(size)})

# Write the Latin square to a file
os.makedirs("CollectedData", exist_ok=True)
with open("CollectedData/configLatinSquare.csv", "w", newline='') as outputFile:
    writer = csv.writer(outputFile, delimiter=';')
    for squareRow in latinSquareConfigs:
        # Write full one user config per row
        row_items = [f"{squareItem['size']},{squareItem['ord']}" for squareItem in squareRow]

        writer.writerow(row_items)
