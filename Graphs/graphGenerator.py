#!/usr/bin/env python3

import csv, sys, json
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path

if len(sys.argv) >= 3:
    user = int(sys.argv[1])  # First argument
    iteration = int(sys.argv[2])  # Second argument
else:
    print("Please provide at least two arguments.")
    exit()


with open('../CollectedData/userData.json', "r") as json_file:
    json_data = json.load(json_file)

try:
    currentTarget = json_data[str(user)]["targets"][str(iteration)]
except KeyError:
    print("Iteration or player not found!")
    exit()
allImages = json_data[str(user)]["imagePos"][str(iteration)]
targePosition = next((index for index, item in enumerate(allImages) if item['image'] == currentTarget), None)
targetRow = targePosition // 4

def normaliseHeight(height, total):
    return (100 - 100*(height / total))

plt.figure(figsize=(10, 7))

timestamps = []
valuesTop = []
valuesBottom = []
targetTopLocations = []
targetBottomLocations = []

with open('../CollectedData/scrollPositions.txt', 'r') as file:
    reader = csv.reader(file, delimiter=';')
    for row in reader:
        if (int(row[0]) == user and int(row[1]) == iteration):
            timestamp = int(row[2])
            totalScroll = float(row[4])
            navbarHeight = float(row[7])
            windowHeight = float(row[6]) - navbarHeight     # account for navbar
            scrollValue = float(row[3]) + navbarHeight
            timestamps.append(timestamp)
            valuesTop.append(100 - 100*(scrollValue / totalScroll))    # percentage not scrolled
            valuesBottom.append(100 - 100*((scrollValue + windowHeight)/ totalScroll))

            FirstRowHeight = float(row[8])
            SecondRowHeight = float(row[9])
            imageHeight = float(row[10])
            targetTopLocations.append(normaliseHeight(FirstRowHeight + targetRow * (SecondRowHeight - FirstRowHeight), totalScroll))
            targetBottomLocations.append(normaliseHeight(imageHeight + FirstRowHeight + targetRow * (SecondRowHeight - FirstRowHeight), totalScroll))


minTime = min(timestamps)
normalisedTime = [((ts - minTime) / 1000) for ts in timestamps]

firstIncorrect = True
firstCorrect = True

with open('../CollectedData/submissions.txt', 'r') as file:     # TODO: remove submission parameters
    reader = csv.reader(file, delimiter=';')
    for row in reader:
        if (int(row[0]) == user and int(row[1]) == iteration):
            subTimestamp = int(row[2])
            
            subTotalScroll = float(row[4])
            subNavbarHeight = float(row[5])
            subScroll = float(row[3]) + subNavbarHeight
            subWindowHeight = float(row[6]) - subNavbarHeight
            subFirstRow = float(row[7])
            subSecondRow = float(row[8])
            subImageHeight = float(row[9])
            subCorrect = int(row[10])
            subClickedImage = row[11]
            if subClickedImage != "SKIP":
                clickedImageRow = next((index for index, item in enumerate(allImages) if item['image'] == subClickedImage), None) // 4
                clickedImageLocation = subFirstRow + clickedImageRow * (subSecondRow - subFirstRow)

            if subCorrect == 0:
                if firstIncorrect:
                    plt.scatter((subTimestamp - minTime) / 1000, 100 - 100*(clickedImageLocation / subTotalScroll), color='red', zorder=3, label='Wrong guess')
                    firstIncorrect = False
                else:
                    plt.scatter((subTimestamp - minTime) / 1000, 100 - 100*(clickedImageLocation / subTotalScroll), color='red', zorder=3)
                plt.scatter((subTimestamp - minTime) / 1000, 100 - 100*((clickedImageLocation + subImageHeight) / subTotalScroll), color='red', zorder=3)
                plt.plot([(subTimestamp - minTime) / 1000, (subTimestamp - minTime) / 1000], [100 - 100*(clickedImageLocation / subTotalScroll), 100 - 100*((clickedImageLocation + subImageHeight) / subTotalScroll)], color='red', zorder=3)
            elif subCorrect == 1:
                if firstCorrect:
                    plt.scatter((subTimestamp - minTime) / 1000, 100 - 100*(clickedImageLocation / subTotalScroll), color='green', zorder=3, label='Correct guess')
                    firstCorrect = False
                else:
                    plt.scatter((subTimestamp - minTime) / 1000, 100 - 100*(clickedImageLocation / subTotalScroll), color='green', zorder=3)
                plt.scatter((subTimestamp - minTime) / 1000, 100 - 100*((clickedImageLocation + subImageHeight) / subTotalScroll), color='green', zorder=3)
                plt.plot([(subTimestamp - minTime) / 1000, (subTimestamp - minTime) / 1000], [100 - 100*(clickedImageLocation / subTotalScroll), 100 - 100*((clickedImageLocation + subImageHeight) / subTotalScroll)], color='green', zorder=3)
            elif subCorrect == 2:
                plt.scatter((subTimestamp - minTime) / 1000, 100 - 100*(subScroll / subTotalScroll), color='blue', zorder=3, label='Skip')

plt.plot(normalisedTime, valuesTop, color='dodgerblue', zorder=2)
plt.plot(normalisedTime, valuesBottom, color='dodgerblue', zorder=2)
plt.fill_between(normalisedTime, valuesTop, valuesBottom, color='skyblue', alpha=0.3, zorder=2, label='Window scroll')

plt.plot(normalisedTime, targetTopLocations, color='lawngreen', zorder=1)
plt.plot(normalisedTime, targetBottomLocations, color='lawngreen', zorder=1)
plt.fill_between(normalisedTime, targetTopLocations, targetBottomLocations, color='palegreen', alpha=0.3, zorder=1, label='Target image')

plt.ylim(-2, 102)
plt.xlabel('Seconds')
plt.ylabel('Scroll')
plt.title('Scroll over time, ordering: ' + json_data[str(user)]["orderings"][str(iteration)] + ", dataset: " + json_data[str(user)]["dataSets"][str(iteration)])
plt.legend()    # TODO: add legend

plt.grid(True)

plt.show()

plt.savefig("graph.png")