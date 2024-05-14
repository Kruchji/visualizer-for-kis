#!/usr/bin/env python3

import csv, sys
import matplotlib.pyplot as plt
from datetime import datetime

if len(sys.argv) >= 3:
    user = int(sys.argv[1])  # First argument
    iteration = int(sys.argv[2])  # Second argument
else:
    print("Please provide at least two arguments.")
    exit()


timestamps = []
valuesTop = []
valuesBottom = []

with open('../scrollPositions.txt', 'r') as file:
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

minTime = min(timestamps)
normalisedTime = [((ts - minTime) / 1000) for ts in timestamps]

plt.plot(normalisedTime, valuesTop, color='dodgerblue')
plt.plot(normalisedTime, valuesBottom, color='dodgerblue')
plt.fill_between(normalisedTime, valuesTop, valuesBottom, color='skyblue', alpha=0.3)
plt.ylim(-2, 102)
plt.xlabel('Seconds')
plt.ylabel('Scroll')
plt.title('Scroll over Time')

plt.grid(True)
plt.show()