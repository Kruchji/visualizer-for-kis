
from constraint import Problem, AllDifferentConstraint
import itertools
import random, math, os, csv, sys
import time

# Get number of solutions from command line arguments
if len(sys.argv) >= 2:
    numOfSolutions = int(sys.argv[1])
else:
    numOfSolutions = 1

# Use constraint library to generate a random Latin square
def generate_random_latin_square(values, max_solutions=1):
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
    random_solution = random.choice(limited_solutions)
    
    # Convert solution dictionary back to 2D array
    latin_square = []
    for row in range(n):
        latin_square.append([random_solution[(row, col)] for col in range(n)])
    
    return latin_square

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

# Repeate config as many times as needed (and make them unique)
repeatedConfigs = []
for i in range(numberOfRepeatConfigs):
    for baseConfig in baseConfigData:
        repeatedConfigs.append((baseConfig['size'], baseConfig['ord'], i))  # Add index to make entries unique

# Generate Latin square
startTime = time.time()
stringLatinSquareConfigs = generate_random_latin_square(repeatedConfigs, max_solutions=numOfSolutions)
print(f"Time taken to generate Latin square: {time.time() - startTime} seconds")
latinSquareConfigs = []
for i in range(len(stringLatinSquareConfigs)):
    latinSquareConfigs.append([])
    attentionChecksAdded = 0
    for j in range(len(stringLatinSquareConfigs[i])):
        # Split the tuple, remove the last element (index), and extract the size and ord
        size, ord, _ = stringLatinSquareConfigs[i][j]  # _ => ignore the last element

        # Add attention check if needed
        if (j + attentionChecksAdded) in attentionCheckIndexes:
            latinSquareConfigs[i].append({"ord": "sp", "size": 4})
            attentionChecksAdded += 1

        latinSquareConfigs[i].append({"ord": ord, "size": int(size)})

# Write the Latin square to a file
with open("CollectedData/.configLatinSquare", "w") as outputFile:
    writer = csv.writer(outputFile, delimiter=';')
    for squareRow in latinSquareConfigs:
        # Write full one user config per row
        row_items = [f"{squareItem['size']},{squareItem['ord']}" for squareItem in squareRow]

        writer.writerow(row_items)

# Read user config to check
"""
uid = 2
configData = []
with open(".configLatinSquare", "r") as configFile:
    reader = csv.reader(configFile, delimiter=';')
    readRows = 0
    for row in reader:
        # Get current user config
        if readRows == int(uid):
            for item in row:
                splitItem = item.split(",")
                configData.append({"ord": splitItem[1], "size": int(splitItem[0])})
            break
        readRows += 1

print(configData)
print(len(configData))
"""