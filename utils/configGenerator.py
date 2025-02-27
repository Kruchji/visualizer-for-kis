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
with open("../backend/configLatinSquare.csv", "w") as outputFile:
    writer = csv.writer(outputFile, delimiter=';')
    for squareRow in latinSquareConfigs:
        # Write full one user config per row
        row_items = [f"{squareItem['size']},{squareItem['ord']}" for squareItem in squareRow]

        writer.writerow(row_items)