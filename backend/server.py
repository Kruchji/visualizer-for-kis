from typing import Annotated
import json, http.server, os, csv, sys
import numpy as np
from urllib.parse import urlparse, parse_qs
from fastapi import APIRouter, FastAPI, Query, Request
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import random


# self-sorting
import selfSort

# Handle admin argument
adminMode = False
if len(sys.argv) >= 2:
    if sys.argv[1] == "--admin":
        adminMode = True
        print("Admin mode enabled!")
       

################## Server ##################
# Create a user config file for a new user - picks one row from the Latin square and permutes the columns
def createUserConfig(uid):
    # First get config row for the user
    userConfigData = []
    with open("configLatinSquare.csv", "r") as configFile:
        reader = csv.reader(configFile, delimiter=';')
        readRows = 0
        for row in reader:
            # Get current user config
            if readRows == uid:
                for item in row:
                    splitItem = item.split(",")
                    userConfigData.append({"ord": splitItem[1], "size": int(splitItem[0])})
                break
            readRows += 1

    # Then add dataset to each config to permute datasets as well later
    for i in range(len(userConfigData)):
        userConfigData[i]["dataset"] = i

    # Now get a random permutation of the user config
    random.shuffle(userConfigData)

    # Finally store the new user config in user's folder as a csv file (each row contains three items)
    with open(f"CollectedData/{uid:04}/userConfig.csv", "w") as configFile:
        writer = csv.writer(configFile, delimiter=';')
        for configRow in userConfigData:
            writer.writerow([configRow["dataset"], configRow["ord"], configRow["size"]])

def getHighestUserID():
    folder_names = [name for name in os.listdir("CollectedData") if os.path.isdir(os.path.join("CollectedData", name))]
    numeric_folders = [int(name) for name in folder_names if name.isdigit()]
    return max(numeric_folders, default=-1)

def createNewUser(prolificPID, studyID, sessionID):
    # get last user ID
    maxUserID = getHighestUserID()

    # get new user ID
    newUid = maxUserID + 1

    logs = {}

    # store new user to .json
    logs[str(newUid)] = {"lastCompleted" : -2, "prolificPID" : prolificPID, "studyID" : studyID, "sessionID" : sessionID, "reloads" : {}}  # -2 to indicate that the user is new
    logsStr = json.dumps(logs, indent=4)
    
    os.makedirs(f"CollectedData/{newUid:04}", exist_ok=True)
    with open(f"CollectedData/{newUid:04}/userData.json", "w") as JSONfile:
        JSONfile.write(logsStr)

    # Also create empty scrollPositions.txt and submissions.txt
    with open(f"CollectedData/{newUid:04}/scrollPositions.txt", "w") as scrollFile:
        pass
    with open(f"CollectedData/{newUid:04}/submissions.txt", "w") as submissionFile:
        pass

    # Also add mapping PID to UID to a csv file (create if it does not exists)
    with open("CollectedData/pid_uid_mapping.csv", "a") as mappingFile:
        writer = csv.writer(mappingFile, delimiter=';')
        writer.writerow([prolificPID, newUid])

        # Also create a user config file
    createUserConfig(newUid)
    return newUid


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.post("/api/newUser")
async def newUser(req: Request):
    params = await req.json()
    # Get Prolific ID, Study ID, and Session ID
    prolificPID = str(params['prolificPID'])
    studyID = str(params['studyID'])
    sessionID = str(params['sessionID'])


    newUid = createNewUser(prolificPID, studyID, sessionID)

    response = {'new_id': newUid, 'numOfSets': len([folder for folder in os.listdir("./Data/")]), 'adminMode' : adminMode}
    response = json.dumps(response).encode('utf-8')
    return response

@app.post("/api/getImages")
async def getImages(req: Request):
    params = await req.json()
    uid = str(params['uid']) if 'uid' in params else None
    iteration = str(params['iteration']) if 'iteration' in params else None
    if uid == None or iteration == None:
        return

    imageSets = [folder for folder in os.listdir("./Data/")]
    imageSets.sort(key=int)

            # load currently saved data
    with open(f"CollectedData/{int(uid):04}/userData.json", "r") as JSONfile:
        logs = json.load(JSONfile)
        userLogs = logs.get(uid,{})
        dataSets = userLogs.get("dataSets",{})

            # load board config from user config file
    configData = []
    with open(f"CollectedData/{int(uid):04}/userConfig.csv", "r") as configFile:
        reader = csv.reader(configFile, delimiter=';')
        for row in reader:
            configData.append({"dataset": int(row[0]), "ord": row[1], "size": int(row[2])})
    # Get size and sorting method for the current iteration
    imagesOnRow = configData[int(iteration) % len(configData)]['size']
    sortingMethod = configData[int(iteration) % len(configData)]['ord']
    if sortingMethod == "ss":
        featuresFileName = "CLIPFeatures.csv"
    elif sortingMethod == "lab":
        featuresFileName = "LABFeatures.csv"

    images = []
    clipFeatures = {}
    if(len(dataSets) < len(imageSets)):
        chosenFolder = imageSets[configData[int(iteration) % len(configData)]['dataset'] % len(imageSets)]

        for file_name in os.listdir("./Data/" + chosenFolder + "/"):
            if file_name.endswith('.jpg'):
                images.append(file_name)
                
        if sortingMethod == "ss" or sortingMethod == "lab":
                    # store features data
            with open("./Data/" + chosenFolder + "/" + featuresFileName, "r") as featuresFile:
                reader = csv.reader(featuresFile, delimiter=';')
                rowID = 0
                for row in reader:
                    clipFeatures[images[rowID]] = row
                    rowID += 1

    else: # end of test - out of dataSets
        chosenFolder = "END"

    lastCompletedIter = userLogs.get("lastCompleted", -2)
    userLogs["lastCompleted"] = lastCompletedIter + 1

    reloads = userLogs.get("reloads",{})
    reloads[lastCompletedIter + 2] = 0
    userLogs["reloads"] = reloads

    logs[uid] = userLogs
    logsStr = json.dumps(logs, indent=4)
            
    with open(f"CollectedData/{int(uid):04}/userData.json", "w") as JSONfile:
        JSONfile.write(logsStr)


    targetImage = ""
    sorted_images = np.array(images)
    if (chosenFolder != "END"):
                # same image for each dataset
        with open("./Data/" + chosenFolder + "/chosenTarget.txt", "r") as targetFile:
            targetImage = targetFile.readline()  

        if sortingMethod == "ss" or sortingMethod == "lab":
                    # Convert the map's arrays from strings to floats
            float_map = {k: np.array(list(map(float, v))) for k, v in clipFeatures.items()}

                    # Collect all float arrays into a single NumPy array
            X = np.array(list(float_map.values()))
                    # We need a 2D array
            X = X.reshape(len(images), -1).astype(np.float32)


            print(f"Sorting images using {sortingMethod} method.")
            _, sorted_images = selfSort.sort_with_flas(X.copy(), images, nc=49, n_images_per_site=imagesOnRow, radius_factor=0.7, wrap=False)

            # send dataset and list of contents back to JS

    response = {'images': images, 'folder' : chosenFolder, 'boardSize' : imagesOnRow, 'sortingMethod' : sortingMethod, 'target' : targetImage, 'ss_images' : sorted_images.tolist()}    
    response = json.dumps(response).encode('utf-8')
    return response




@app.post("/api/scrollPositions")
async def scrollPositions(req: Request):
    request = await req.json()
    uid = str(request["uid"])
    iteration = str(request["iteration"])
    logJSON = json.loads(request["log"])
    scrollData = logJSON["multipleScrollData"]
    toLogText = ""
    for scrollLog in scrollData:
        toLogText += str(uid)+";"+str(iteration)+";"+str(scrollLog["timestamp"])+";"+str(scrollLog["scrollPos"])+";"+str(scrollLog["totalScroll"])+";"+str(scrollLog["windowW"])+";"+str(scrollLog["windowH"])+";"+str(scrollLog["navbarH"])+";"+str(scrollLog["firstRowStart"])+";"+str(scrollLog["secondRowStart"])+";"+str(scrollLog["imageHeight"])+";"+str(scrollLog["missedTarget"])+";"+str(scrollLog["afterLoad"])+"\n"
    with open(f"CollectedData/{int(uid):04}/scrollPositions.txt", 'a') as csvFile:
        csvFile.write(toLogText)
    
    response = {}
    response = json.dumps(response).encode('utf-8')
    return response


@app.post("/api/submissions")
async def submissions(req: Request):
    request = await req.json()
    uid = str(request["uid"])
    iteration = request["iteration"]
    logJSON = request
    toLogText = str(uid)+";"+str(iteration)+";"+str(logJSON["timestamp"])+";"+str(logJSON["scrollPos"])+";"+str(logJSON["totalScroll"])+";"+str(logJSON["navbarH"])+";"+str(logJSON["windowH"])+";"+str(logJSON["firstRowStart"])+";"+str(logJSON["secondRowStart"])+";"+str(logJSON["imageHeight"])+";"+str(logJSON["correct"])+";"+str(logJSON["image"])+"\n"

    # write csv data to disk
    with open(f"CollectedData/{int(uid):04}/submissions.txt", 'a') as csvFile:
        csvFile.write(toLogText)
    
    response = {}
    response = json.dumps(response).encode('utf-8')
    return response

@app.post("/api/oldUser")
async def oldUser(req: Request):
    request = await req.json()
    # Get Prolific PID
    prolificPID = request["prolificPID"]
    loadFailed = 0

                # Get user ID from mapping file
    oldUser = "-1"

    # Check if file exists, if not create it
    if not os.path.exists("CollectedData/pid_uid_mapping.csv"):
        with open("CollectedData/pid_uid_mapping.csv", "w") as f:
            pass  # Creates an empty file
    try:
        with open("CollectedData/pid_uid_mapping.csv", "r") as mappingFile:
            reader = csv.reader(mappingFile, delimiter=';')
            for row in reader:
                if row[0] == prolificPID:
                    oldUser = row[1]
                    break
    except FileNotFoundError:
        pass

    if oldUser == "-1":
        loadFailed = 1
        userLogs = {}


    try:
        with open(f"CollectedData/{int(oldUser):04}/userData.json", "r") as JSONfile:
            logs = json.load(JSONfile)
            userLogs = logs[str(oldUser)]
    except Exception as e:  # file empty
        loadFailed = 1
        userLogs = {}
            
    lastCompletedIter = userLogs.get("lastCompleted", -1)
    userLogs["lastCompleted"] = lastCompletedIter
    currIter = str(lastCompletedIter + 1)

    reloads = userLogs.get("reloads",{})
    reloads[currIter] = reloads.get(str(currIter), 0) + 1
    userLogs["reloads"] = reloads

    if (loadFailed == 0):
        # update user data in json
        logs[str(oldUser)] = userLogs
        logsStr = json.dumps(logs, indent=4)
                
        with open(f"CollectedData/{int(oldUser):04}/userData.json", "w") as JSONfile:
            JSONfile.write(logsStr)

    response = {'loadFailed': loadFailed, 'userID' : oldUser, 'currIter' : int(currIter),'currImages' : [item['image'] for item in userLogs.get("imagePos", {}).get(currIter, [])], 'currTarget' : userLogs.get("targets", {}).get(currIter, "END"), 'currBoardSize' : userLogs.get("imagesPerRow", {}).get(currIter, 4), 'currDataFolder' : userLogs.get("dataSets", {}).get(currIter, "END"), 'currOrdering' : userLogs.get("orderings", {}).get(currIter, "missing"), 'numOfSets': len([folder for folder in os.listdir("./Data/")]), 'adminMode' : adminMode}
    response = json.dumps(response).encode('utf-8')
    return response


@app.post("/api/imageConfig")
async def imageConfig(req: Request):
    jsonPayload = await req.json()

    
    positions = json.loads(jsonPayload["positions"])
    uid = str(jsonPayload["uid"])
    iteration = str(jsonPayload["iteration"])
    target = jsonPayload["target"]
    dataSet = jsonPayload["dataSet"]
    ordering = jsonPayload["ordering"]
    perRow = jsonPayload["perRow"]
            
            # load currently saved data
    with open(f"CollectedData/{int(uid):04}/userData.json", "r") as JSONfile:
        
        logs = json.load(JSONfile)
        userLogs = logs.get(uid,{})

    # write new data
    posData = userLogs.get("imagePos",{})
    posData[iteration] = positions
    userLogs["imagePos"] = posData

    targetsData = userLogs.get("targets",{})
    targetsData[iteration] = target
    userLogs["targets"] = targetsData

    dataSets = userLogs.get("dataSets",{})
    dataSets[iteration] = dataSet
    userLogs["dataSets"] = dataSets

    orderings = userLogs.get("orderings",{})
    orderings[iteration] = ordering
    userLogs["orderings"] = orderings

    imagesPerRow = userLogs.get("imagesPerRow",{})
    imagesPerRow[iteration] = perRow
    userLogs["imagesPerRow"] = imagesPerRow
            
    # save new data in JSON file
    logs[uid] = userLogs
    logsStr = json.dumps(logs, indent=4)
    with open(f"CollectedData/{int(uid):04}/userData.json", "w") as JSONfile:
       
        JSONfile.write(logsStr)

    response = {}
    response = json.dumps(response).encode('utf-8')
    return response
    

@app.get("/health")
async def health():
    return {"status": "ok"}
