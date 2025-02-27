
from constraint import Problem, AllDifferentConstraint
import itertools
import random, math, os, csv, sys
import time
import numpy as np

# Get number of solutions from command line arguments
if len(sys.argv) >= 2:
    numOfSolutions = int(sys.argv[1])
else:
    numOfSolutions = 1000

# Use constraint library to generate a random Latin square
def generate_random_latin_square(values, configSize, numOfDatasets, max_solutions=1, numOfUsers=126):
    n = len(values)
    problem = Problem()

    # Variable for each cell in the Latin square
    for row in range(n):
        for col in range(n):
            problem.addVariable((row, col), values)
    
    # All rows must be unique
    for row in range(n):
        problem.addConstraint(AllDifferentConstraint(), [(row, col) for col in range(n)])
    
    # All columns must be unique
    for col in range(n):
        problem.addConstraint(AllDifferentConstraint(), [(row, col) for row in range(n)])
    
    # getSolutionIter => lazily evaluate solutions (and limit the number)
    solution_iterator = problem.getSolutionIter()
    limited_solutions = list(itertools.islice(solution_iterator, max_solutions))

    if not limited_solutions:
        raise ValueError("No Latin square possible with the given values.")
    
    # Randomly pick one of the solutions
    random_solutions = random.sample(limited_solutions, (math.ceil(numOfUsers / configSize)) * (math.ceil(numOfDatasets / configSize))) # number of users / config size * number of datasets / config size
    
    # Convert solution dictionaries back to 2D array (numpy) and store them in a list
    latin_squares = []
    for random_solution in random_solutions:
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
datasetFolders = [folder for folder in os.listdir("./Data/")]
datasetFolders.sort(key=int)

# For each folder check if number of .jpg images is less than or equal to 16 => attention check
attentionCheckIndexes = []
for folder in datasetFolders:
    imageCount = len([file for file in os.listdir(f"./Data/{folder}") if file.endswith(".jpg")])
    if imageCount <= 16:
        attentionCheckIndexes.append(datasetFolders.index(folder))

# Get number of not attention check datasets
numberOfRealDatasets = len(datasetFolders) - len(attentionCheckIndexes)
numberOfRepeatConfigs = math.ceil((numberOfRealDatasets) / baseConfigLength)    # Generate enough to cover all datasets

# Define number of users
users = 126

# Make base configs unique
uniqueConfigs = []
for i, baseConfig in enumerate(baseConfigData):
    uniqueConfigs.append((baseConfig['size'], baseConfig['ord'], i))  # Add index to make entries unique

# Generate Latin squares
startTime = time.time()
generatedLatinSquareList = generate_random_latin_square(uniqueConfigs, baseConfigLength, numberOfRealDatasets, max_solutions=numOfSolutions, numOfUsers=users)
print(f"Time taken to generate {numOfSolutions} Latin squares: {time.time() - startTime} seconds")

# Combine smaller latin squares into one large one
latinSquareGrid = np.array(generatedLatinSquareList).reshape(math.ceil(users / baseConfigLength), math.ceil(numberOfRealDatasets / baseConfigLength), baseConfigLength, baseConfigLength)
largeLatinSquareRows = [np.hstack(row) for row in latinSquareGrid]
largeGeneratedLatinSquare = np.vstack(largeLatinSquareRows)

# Insert attention checks into the Latin square and remove the last element (index)
latinSquareConfigs = []
for i in range(len(largeGeneratedLatinSquare)):
    latinSquareConfigs.append([])
    attentionChecksAdded = 0
    for j in range(len(largeGeneratedLatinSquare[i])):
        # Split the tuple, remove the last element (index), and extract the size and ord
        size, ord, _ = largeGeneratedLatinSquare[i][j]  # _ => ignore the last element

        # Add attention check if needed
        if (j + attentionChecksAdded) in attentionCheckIndexes:
            latinSquareConfigs[i].append({"ord": "sp", "size": 4})
            attentionChecksAdded += 1

        latinSquareConfigs[i].append({"ord": ord, "size": int(size)})

# Write the Latin square to a file
with open("CollectedData/configLatinSquare.csv", "w") as outputFile:
    writer = csv.writer(outputFile, delimiter=';')
    for squareRow in latinSquareConfigs:
        # Write full one user config per row
        row_items = [f"{squareItem['size']},{squareItem['ord']}" for squareItem in squareRow]

        writer.writerow(row_items)
