#!/usr/bin/env python3

import json, http.server, os, csv, sys
import numpy as np
from urllib.parse import urlparse, parse_qs
import random

# self-sorting
from Libs import LAS_FLAS

# Handle admin argument
adminMode = False
if len(sys.argv) >= 2:
    if sys.argv[1] == "--admin":
        adminMode = True
        print("Admin mode enabled!")

################## Server ##################

def getHighestUserID():
    folder_names = [name for name in os.listdir("CollectedData") if os.path.isdir(os.path.join("CollectedData", name))]
    numeric_folders = [int(name) for name in folder_names if name.isdigit()]
    return max(numeric_folders, default=-1)

# Create a user config file for a new user - picks one row from the Latin square and permutes the columns
def createUserConfig(uid):
    # First get config row for the user
    userConfigData = []
    with open("CollectedData/configLatinSquare.csv", "r") as configFile:
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

    # Get number of datasets
    datasetCount = len([folder for folder in os.listdir("./Data/") if os.path.isdir(os.path.join("./Data/", folder))])

    # Get all attention check dataset indices (each line in file)
    attentionCheckIndices = []
    if os.path.isfile("./Data/attentionCheckIndices.txt"):
        with open("./Data/attentionCheckIndices.txt", "r") as attentionCheckFile:
            for line in attentionCheckFile:
                datasetIndex = int(line.strip())
                if not datasetIndex in attentionCheckIndices:
                    attentionCheckIndices.append(datasetIndex)
    
    # Get number of attention checks
    numOfAttentionChecks = len(attentionCheckIndices)
    realDatasetCount = datasetCount - numOfAttentionChecks  # Actual full datasets

    # Then add (real) dataset to each config - skipping the attention check indices
    realDatasetIndex = 0
    for i in range(datasetCount):
        if i not in attentionCheckIndices:
            if realDatasetIndex < len(userConfigData):
                userConfigData[realDatasetIndex]["dataset"] = i
                realDatasetIndex += 1
    
    # Taky only the real dataset count elements from the user config
    userConfigData = userConfigData[:realDatasetCount]

    # Now get a random permutation of the user config (real datasets only)
    random.shuffle(userConfigData)

    # Insert back attention checks (ord = sp and size = 4) evenly into the user config
    for i in range(len(attentionCheckIndices)):
        # e.g. for 3 attention checks, insert at 1/4, 2/4, 3/4
        userConfigData.insert(int((i+1) * datasetCount / (numOfAttentionChecks + 1)), {"dataset": attentionCheckIndices[i], "ord": "sp", "size": 4})

    # Finally store the new user config in user's folder as a csv file (each row contains three items)
    with open(f"CollectedData/{uid:04}/userConfig.csv", "w") as configFile:
        writer = csv.writer(configFile, delimiter=';')
        for configRow in userConfigData:
            writer.writerow([configRow["dataset"], configRow["ord"], configRow["size"]])
    
    print(f"User config created for user {uid}.")

def createNewUser(prolificPID, studyID, sessionID):
    # get last user ID
    maxUserID = getHighestUserID()

    # get new user ID
    newUid = maxUserID + 1

    logs = {}

    # store new user to .json
    logs[str(newUid)] = {"lastCompleted" : -2, "PROLIFIC_PID" : prolificPID, "STUDY_ID" : studyID, "SESSION_ID" : sessionID, "reloads" : {}, "totalIncorrect" : 0}  # -2 to indicate that the user is new
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


class TrackingServer (http.server.SimpleHTTPRequestHandler):

    def do_POST(self):
        
        # get user ID and iteration from URL
        query_params = parse_qs(urlparse(self.path).query)
        try:
            uid = str(int(query_params.get("uid", [0])[0]))
            iteration = str(int(query_params.get("iteration", [0])[0]))
        except (KeyError, ValueError) as e:
            # bad parameters
            uid = "-1"
            iteration = "-1"

        # decide next action based on request URL


        ############### Create a new user ###############
        if self.path.startswith('/newUser'):
            # Get Prolific ID, Study ID, and Session ID
            prolificPID = query_params.get("PROLIFIC_PID", [""])[0]
            studyID = query_params.get("STUDY_ID", [""])[0]
            sessionID = query_params.get("SESSION_ID", [""])[0]

            newUid = createNewUser(prolificPID, studyID, sessionID)

            # send new user ID to JS
            self.send_response(200) 
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            response = {'new_id': newUid, 'numOfSets': len([folder for folder in os.listdir("./Data/") if os.path.isdir(os.path.join("./Data/", folder))]), 'adminMode' : adminMode}
            self.wfile.write(json.dumps(response).encode('utf-8'))

            return
        

        ############### Load existing user ###############
        if self.path.startswith('/oldUser'):    
            # Get Prolific PID
            prolificPID = query_params.get("PROLIFIC_PID", [""])[0]

            loadFailed = 0

            # Get user ID from mapping file
            oldUser = "-1"
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

            # Check if the user has already completed all datasets (set to "END")
            imageSets = [folder for folder in os.listdir("./Data/") if os.path.isdir(os.path.join("./Data/", folder))]
            
            if lastCompletedIter >= len(imageSets) - 1:
                currentDataFolder = "END"
                currentTarget = "END"
                currOrdering = "END"
            else:
                # Get the current dataset and target image for the user (or "MISSING" if not found - user will request new config)
                currentDataFolder = userLogs.get("dataSets",{}).get(currIter, "MISSING")
                currentTarget = userLogs.get("targets", {}).get(currIter, "MISSING")
                currOrdering = userLogs.get("orderings", {}).get(currIter, "MISSING")

            if (loadFailed == 0):
                # update user data in json
                logs[str(oldUser)] = userLogs
                logsStr = json.dumps(logs, indent=4)
                
                with open(f"CollectedData/{int(oldUser):04}/userData.json", "w") as JSONfile:
                    JSONfile.write(logsStr)

            # send new user ID to JS
            self.send_response(200) 
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            
            response = {'loadFailed': loadFailed, 'userID' : oldUser, 'currIter' : int(currIter),'currImages' : [item['image'] for item in userLogs.get("imagePos", {}).get(currIter, [])], 'currTarget' : currentTarget, 'currBoardSize' : userLogs.get("imagesPerRow", {}).get(currIter, 4), 'currDataFolder' : currentDataFolder, 'currOrdering' : currOrdering, 'numOfSets': len([folder for folder in os.listdir("./Data/") if os.path.isdir(os.path.join("./Data/", folder))]), 'adminMode' : adminMode, 'totalIncorrect' : userLogs.get("totalIncorrect", 0)}
            self.wfile.write(json.dumps(response).encode('utf-8'))

            return

        ############### Get images in a folder ###############
        elif self.path.startswith('/getImages'):    
            imageSets = [folder for folder in os.listdir("./Data/") if os.path.isdir(os.path.join("./Data/", folder))]
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

                # Get list of only .jpg files in the folder
                images = [file_name for file_name in os.listdir("./Data/" + chosenFolder + "/") if file_name.endswith('.jpg')]

                # Sort the images by name (to ensure consistent order across different platforms)
                images.sort()
                
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

            # update progress and reloads in user data
            lastCompletedIter = userLogs.get("lastCompleted", -1)
            print(lastCompletedIter, iteration)
            if lastCompletedIter < int(iteration):  # to not decrease progress counter
                userLogs["lastCompleted"] = int(iteration) - 1

            reloads = userLogs.get("reloads",{})
            reloads[int(iteration)] = reloads.get(str(iteration), 0)
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
                    _, sorted_images = LAS_FLAS.sort_with_flas(X.copy(), images, nc=49, n_images_per_site=imagesOnRow, radius_factor=0.7, wrap=False)

            # send dataset and list of contents back to JS 
            self.send_response(200) 
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            response = {'images': images, 'folder' : chosenFolder, 'boardSize' : imagesOnRow, 'sortingMethod' : sortingMethod, 'target' : targetImage, 'ss_images' : sorted_images.tolist()}
            self.wfile.write(json.dumps(response).encode('utf-8'))

            return


        ############### Store newly generated grid / layout of images ###############
        elif self.path.startswith('/imageConfig'):
            # load received JSON data
            contentLength = int(self.headers.get('content-length'))
            decodedData = self.rfile.read(contentLength).decode()
            jsonPayload = json.loads(decodedData)

            positions = json.loads(jsonPayload["positions"])
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
            self.send_response(200) 


        ############### Track scrollbar position ###############
        elif self.path.startswith('/scrollPositions'):
            # load received JSON data
            contentLength = int(self.headers.get('content-length'))
            decodedData = self.rfile.read(contentLength).decode()
            logJSON = json.loads(decodedData)

            scrollData = logJSON["multipleScrollData"]

            # convert to csv
            toLogText = ""
            for scrollLog in scrollData:
                toLogText += str(uid)+";"+str(iteration)+";"+str(scrollLog["timestamp"])+";"+str(scrollLog["scrollPos"])+";"+str(scrollLog["totalScroll"])+";"+str(scrollLog["windowW"])+";"+str(scrollLog["windowH"])+";"+str(scrollLog["navbarH"])+";"+str(scrollLog["firstRowStart"])+";"+str(scrollLog["secondRowStart"])+";"+str(scrollLog["imageHeight"])+";"+str(scrollLog["missedTarget"])+";"+str(scrollLog["afterLoad"])+"\n"

            # write csv data to disk
            with open(f"CollectedData/{int(uid):04}/scrollPositions.txt", 'a') as csvFile:
                csvFile.write(toLogText)
            self.send_response(200)


        ############### Store submission attempts ###############
        elif self.path.startswith('/submissions'):
            # load received JSON data
            contentLength = int(self.headers.get('content-length'))
            decodedData = self.rfile.read(contentLength).decode()
            logJSON = json.loads(decodedData)

            # correctness values: 0 = incorrect, 1 = correct, 2 = compare

            # convert to csv
            toLogText = str(uid)+";"+str(iteration)+";"+str(logJSON["timestamp"])+";"+str(logJSON["scrollPos"])+";"+str(logJSON["totalScroll"])+";"+str(logJSON["navbarH"])+";"+str(logJSON["windowH"])+";"+str(logJSON["firstRowStart"])+";"+str(logJSON["secondRowStart"])+";"+str(logJSON["imageHeight"])+";"+str(logJSON["correct"])+";"+str(logJSON["image"])+"\n"

            # write csv data to disk
            with open(f"CollectedData/{int(uid):04}/submissions.txt", 'a') as csvFile:
                csvFile.write(toLogText)

            # If the submission was incorrect (0), increment the total incorrect counter
            if logJSON["correct"] == 0:
                # load currently saved data
                with open(f"CollectedData/{int(uid):04}/userData.json", "r") as JSONfile:
                    logs = json.load(JSONfile)
                    userLogs = logs.get(uid,{})

                userLogs["totalIncorrect"] = userLogs.get("totalIncorrect", 0) + 1

                # save new data in JSON file
                logs[uid] = userLogs
                logsStr = json.dumps(logs, indent=4)
                
                with open(f"CollectedData/{int(uid):04}/userData.json", "w") as JSONfile:
                    JSONfile.write(logsStr)

            self.send_response(200)


        # general send response
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        return




if __name__ == '__main__':
    # http.server.test(TrackingServer, http.server.HTTPServer, port=8001)   # for local testing (prints to console)

    server_address = ('', 8001)  # Bind to all available IP addresses on the host
    httpd = http.server.HTTPServer(server_address, TrackingServer)
    
    print("Server running on port 8001, accessible to local network.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down the server...")
        httpd.server_close()  # Close the server socket
        print("Server stopped.")
