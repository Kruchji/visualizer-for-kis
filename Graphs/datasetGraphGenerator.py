#!/usr/bin/env python3

import csv, sys, json
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# returns reverse percentage of current height (scroll)
def normaliseHeight(currHeight, totalHeight):
    return (100 - 100*(currHeight / totalHeight))

# dataset and ordering must be specified
if len(sys.argv) >= 3:
    dataset = sys.argv[1]       # First argument
    ordering = sys.argv[2]      # Second argument
else:
    print("Please provide at least two arguments. (dataset, ordering, to_file)")
    exit()

# load user data
with open('../CollectedData/userData.json', "r") as json_file:
    all_user_data = json.load(json_file)

# plot window size
plt.figure(figsize=(10, 7))
fig, ax = plt.subplots()

validUsers = []

# iterate over all users, pick the ones that have the requested dataset and ordering
for user in all_user_data:
    user_data_sets = all_user_data[user]["dataSets"]
    user_orderings = all_user_data[user]["orderings"]

    # check if this user has the requested dataset and ordering
    iteration_num = None
    for key, value in user_data_sets.items():
        if value == dataset:
            iteration_num = key
            break
    
    # user has not completed this dataset
    if iteration_num is None:
        continue

    # user has completed this dataset on a different ordering
    if user_orderings[iteration_num] != ordering:
        continue

    validUsers.append(user)


# to prevent multiple labels
firstIncorrect = True
firstCorrect = True
firstCompare = True
firstSkip = True
firstTargetOverlay = True
firstLoadLine = True

# iterate over all valid users
currentUser = 0
for user in validUsers:
    ### Valid user data ###
    currentUser += 1

    # get data about target image
    currentTarget = all_user_data[user]["targets"][iteration_num]
    allImages = all_user_data[user]["imagePos"][iteration_num]
    imagesPerRow = all_user_data[user]["imagesPerRow"][iteration_num]
    targePosition = next((index for index, item in enumerate(allImages) if item['image'] == currentTarget), None)   # find position of target in grid
    targetRow = targePosition // imagesPerRow      # 4 or 8 images per row

    # get scroll position data
    timestamps = []
    valuesTop = []
    valuesBottom = []
    targetTopLocations = []
    targetBottomLocations = []

    previousCompare = {"x" : 0, "y" : 0, "height" : 0}
    previousTargetOverlay = {"x" : 0}

    with open('../CollectedData/scrollPositions.txt', 'r') as file:
        

        reader = csv.reader(file, delimiter=';')
        for row in reader:
            if (int(row[0]) == int(user) and int(row[1]) == int(iteration_num)):
                timestamp = int(row[2])
                totalScroll = float(row[4])
                navbarHeight = float(row[7])
                windowHeight = float(row[6]) - navbarHeight     # account for navbar
                scrollValue = float(row[3]) + navbarHeight      # account for navbar

                # viewport position
                timestamps.append(timestamp)
                valuesTop.append(normaliseHeight(scrollValue, totalScroll))    # percentage not scrolled
                valuesBottom.append(normaliseHeight(scrollValue + windowHeight,  totalScroll))

                FirstRowHeight = float(row[8])
                SecondRowHeight = float(row[9])
                imageHeight = float(row[10])

                # get difference between rows to calculate position of target
                targetTopLocations.append(normaliseHeight(FirstRowHeight + targetRow * (SecondRowHeight - FirstRowHeight), totalScroll))
                targetBottomLocations.append(normaliseHeight(imageHeight + FirstRowHeight + targetRow * (SecondRowHeight - FirstRowHeight), totalScroll))

                

    # get time to start from 0
    minTime = min(timestamps)
    normalisedTime = [((ts - minTime) / 1000) for ts in timestamps]

    
    # draw red line to mark reloads
    lastTimestamp = normalisedTime[0]
    for normTimestamp in normalisedTime:
        if (normTimestamp - lastTimestamp > 1.5):
            if(firstLoadLine):
                plt.axvline(x=lastTimestamp, color='red', linestyle='--', label='Unload/load', alpha=(1/len(validUsers)))
                firstLoadLine = False
            else:
                plt.axvline(x=lastTimestamp, color='red', linestyle='--', alpha=(1/len(validUsers)))
            plt.axvline(x=normTimestamp, color='red', linestyle='--', alpha=(1/len(validUsers)))

        lastTimestamp = normTimestamp


    with open('../CollectedData/submissions.txt', 'r') as file:
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            if (int(row[0]) == int(user) and int(row[1]) == int(iteration_num)):
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

                if subCorrect < 3:
                    # get position of clicked image
                    clickedImageRow = next((index for index, item in enumerate(allImages) if item['image'] == subClickedImage), None) // imagesPerRow
                    clickedImageLocation = subFirstRow + clickedImageRow * (subSecondRow - subFirstRow)

                # display dot based on submission type, time and image position
                # incorrect
                if subCorrect == 0:
                    # for label display
                    if firstIncorrect:
                        plt.scatter((subTimestamp - minTime) / 1000, normaliseHeight(clickedImageLocation, subTotalScroll), color='red', zorder=3, label='Wrong guess', alpha=(1/len(validUsers)))
                        firstIncorrect = False
                    else:
                        plt.scatter((subTimestamp - minTime) / 1000, normaliseHeight(clickedImageLocation, subTotalScroll), color='red', zorder=3, alpha=(1/len(validUsers)))

                    plt.scatter((subTimestamp - minTime) / 1000, normaliseHeight(clickedImageLocation + subImageHeight, subTotalScroll), color='red', zorder=3, alpha=(1/len(validUsers)))
                    plt.plot([(subTimestamp - minTime) / 1000, (subTimestamp - minTime) / 1000], [normaliseHeight(clickedImageLocation, subTotalScroll), normaliseHeight(clickedImageLocation + subImageHeight, subTotalScroll)], color='red', zorder=3, alpha=(1/len(validUsers)))

                # correct
                elif subCorrect == 1:
                    # for label display
                    if firstCorrect:
                        plt.scatter((subTimestamp - minTime) / 1000, normaliseHeight(clickedImageLocation, subTotalScroll), color='green', zorder=3, label='Correct guess', alpha=(1/len(validUsers)))
                        firstCorrect = False
                    else:
                        plt.scatter((subTimestamp - minTime) / 1000, normaliseHeight(clickedImageLocation, subTotalScroll), color='green', zorder=3, alpha=(1/len(validUsers)))

                    plt.scatter((subTimestamp - minTime) / 1000, normaliseHeight(clickedImageLocation + subImageHeight, subTotalScroll), color='green', zorder=3, alpha=(1/len(validUsers)))
                    plt.plot([(subTimestamp - minTime) / 1000, (subTimestamp - minTime) / 1000], [normaliseHeight(clickedImageLocation, subTotalScroll), normaliseHeight(clickedImageLocation + subImageHeight, subTotalScroll)], color='green', zorder=3, alpha=(1/len(validUsers)))

                # compare
                elif subCorrect == 2:
                    # for label display
                    if firstCompare:
                        plt.scatter((subTimestamp - minTime) / 1000, normaliseHeight(clickedImageLocation, subTotalScroll), color='blue', zorder=3, label='Compare use', alpha=(1/len(validUsers)))
                        firstCompare = False
                    else:
                        plt.scatter((subTimestamp - minTime) / 1000, normaliseHeight(clickedImageLocation, subTotalScroll), color='blue', zorder=3, alpha=(1/len(validUsers)))

                    plt.scatter((subTimestamp - minTime) / 1000, normaliseHeight(clickedImageLocation + subImageHeight, subTotalScroll), color='blue', zorder=3, alpha=(1/len(validUsers)))
                    plt.plot([(subTimestamp - minTime) / 1000, (subTimestamp - minTime) / 1000], [normaliseHeight(clickedImageLocation, subTotalScroll), normaliseHeight(clickedImageLocation + subImageHeight, subTotalScroll)], color='blue', zorder=3, alpha=(1/len(validUsers)))

                    previousCompare['x'] = (subTimestamp - minTime) / 1000
                    previousCompare['y'] = normaliseHeight(clickedImageLocation, subTotalScroll)
                    previousCompare['height'] = normaliseHeight(clickedImageLocation + subImageHeight, subTotalScroll) - previousCompare['y']
                
                # compare end
                elif subCorrect == 3:
                    rectWidth = ((subTimestamp - minTime) / 1000) - previousCompare['x']
                    rectangle = patches.Rectangle((previousCompare['x'], previousCompare['y']), rectWidth, previousCompare['height'], linewidth=1, edgecolor='darkgray', facecolor='lightgray', alpha=(1/len(validUsers)))
                    ax.add_patch(rectangle)

                # skip
                elif subCorrect == 4:
                    # for label display
                    if firstSkip:
                        plt.scatter((subTimestamp - minTime) / 1000, normaliseHeight(0, subTotalScroll), color='hotpink', zorder=3, label='Skip', alpha=(1/len(validUsers)))
                        firstSkip = False
                    else:
                        plt.scatter((subTimestamp - minTime) / 1000, normaliseHeight(0, subTotalScroll), color='hotpink', zorder=3, alpha=(1/len(validUsers)))

                    plt.scatter((subTimestamp - minTime) / 1000, normaliseHeight(subTotalScroll, subTotalScroll), color='hotpink', zorder=3, alpha=(1/len(validUsers)))
                    plt.plot([(subTimestamp - minTime) / 1000, (subTimestamp - minTime) / 1000], [normaliseHeight(0, subTotalScroll), normaliseHeight(subTotalScroll, subTotalScroll)], color='hotpink', zorder=3, alpha=(1/len(validUsers)))

                # target overlay
                elif subCorrect == 5:
                    # for label display
                    if firstTargetOverlay:
                        plt.scatter((subTimestamp - minTime) / 1000, normaliseHeight(0, subTotalScroll), color='cyan', zorder=3, label='Target overlay', alpha=(1/len(validUsers)))
                        firstTargetOverlay = False
                    else:
                        plt.scatter((subTimestamp - minTime) / 1000, normaliseHeight(0, subTotalScroll), color='cyan', zorder=3, alpha=(1/len(validUsers)))

                    plt.scatter((subTimestamp - minTime) / 1000, normaliseHeight(subTotalScroll, subTotalScroll), color='cyan', zorder=3, alpha=(1/len(validUsers)))
                    plt.plot([(subTimestamp - minTime) / 1000, (subTimestamp - minTime) / 1000], [normaliseHeight(0, subTotalScroll), normaliseHeight(subTotalScroll, subTotalScroll)], color='cyan', zorder=3, alpha=(1/len(validUsers)))

                    previousTargetOverlay['x'] = (subTimestamp - minTime) / 1000
                
                # target overlay end
                elif subCorrect == 6:
                    rectWidth = ((subTimestamp - minTime) / 1000) - previousTargetOverlay['x']
                    rectangle = patches.Rectangle((previousTargetOverlay['x'], normaliseHeight(0, subTotalScroll)), rectWidth, normaliseHeight(subTotalScroll, subTotalScroll) - normaliseHeight(0, subTotalScroll), linewidth=1, edgecolor='darkturquoise', facecolor='lightgray', alpha=(1/len(validUsers)))
                    ax.add_patch(rectangle)


    # draw viewport locations
    plt.plot(normalisedTime, valuesTop, color='dodgerblue', zorder=2, alpha=(1/len(validUsers)))
    plt.plot(normalisedTime, valuesBottom, color='dodgerblue', zorder=2, alpha=(1/len(validUsers)))
    if currentUser == 1:
        plt.fill_between(normalisedTime, valuesTop, valuesBottom, color='skyblue', alpha=0.3 * (1/len(validUsers)), zorder=2, label='Viewport scroll')
    else:
        plt.fill_between(normalisedTime, valuesTop, valuesBottom, color='skyblue', alpha=0.3 * (1/len(validUsers)), zorder=2)

    # draw target image locations
    plt.plot(normalisedTime, targetTopLocations, color='lawngreen', zorder=1, alpha=(1/len(validUsers)))
    plt.plot(normalisedTime, targetBottomLocations, color='lawngreen', zorder=1, alpha=(1/len(validUsers)))
    if currentUser == 1:
        plt.fill_between(normalisedTime, targetTopLocations, targetBottomLocations, color='palegreen', alpha=0.3 * (1/len(validUsers)), zorder=1, label='Target image')
    else:
        plt.fill_between(normalisedTime, targetTopLocations, targetBottomLocations, color='palegreen', alpha=0.3 * (1/len(validUsers)), zorder=1)

# stay in percentage range
plt.ylim(-2, 102)

# plot labels
plt.xlabel('Seconds')
plt.ylabel('Percentage not scrolled')
plt.title('Scroll over time, ordering: ' + str(ordering) + ", images/row: " + str(imagesPerRow) + ", dataset: " + str(dataset))
plt.legend()

plt.grid(True)  # background grid

# show plot (or save to file)
if len(sys.argv) >= 4 and int(sys.argv[3]) == 1:
    plt.savefig("multiGraph.png")
else:
    plt.show()
