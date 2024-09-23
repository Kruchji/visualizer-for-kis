#!/usr/bin/env python3

import json, http.server, os, csv
import numpy as np
from urllib.parse import urlparse, parse_qs

# self-sorting
import selfSort


################## Server ##################

def createNewUser():
    newUid = 0
    try:
        with open("CollectedData/userData.json", "r") as fh:
            logs = json.load(fh)
            newUid = max(map(int, logs.keys())) + 1     # gets last known user and increments its ID
    except json.JSONDecodeError:  # file empty
        logs = {}

    # store new user to .json
    logs[str(newUid)] = {"lastCompleted" : -2}
    logsStr = json.dumps(logs, indent=4)
    
    with open("CollectedData/userData.json", "w") as JSONfile:
        JSONfile.write(logsStr)

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
            newUid = createNewUser()

            # send new user ID to JS
            self.send_response(200) 
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            response = {'new_id': newUid, 'numOfSets': len([folder for folder in os.listdir("./Data/")])}
            self.wfile.write(json.dumps(response).encode('utf-8'))

            return
        

        ############### Load existing user ###############
        if self.path.startswith('/oldUser'):    
            # load received JSON data
            contentLength = int(self.headers.get('content-length'))
            decodedData = self.rfile.read(contentLength).decode()
            jsonPayload = json.loads(decodedData)

            oldUser = jsonPayload["oldUserID"]
            loadFailed = 0
            try:
                with open("CollectedData/userData.json", "r") as JSONfile:
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
                
                with open("CollectedData/userData.json", "w") as JSONfile:
                    JSONfile.write(logsStr)

            # send new user ID to JS
            self.send_response(200) 
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            
            response = {'loadFailed': loadFailed, 'currIter' : int(currIter),'currImages' : [item['image'] for item in userLogs.get("imagePos", {}).get(currIter, [])], 'currTarget' : userLogs.get("targets", {}).get(currIter, "END"), 'currBoardSize' : userLogs.get("imagesPerRow", {}).get(currIter, 4), 'currDataFolder' : userLogs.get("dataSets", {}).get(currIter, "END"), 'numOfSets': len([folder for folder in os.listdir("./Data/")])}
            self.wfile.write(json.dumps(response).encode('utf-8'))

            return

        ############### Get images in a folder ###############
        elif self.path.startswith('/getImages'):    
            imageSets = [folder for folder in os.listdir("./Data/")]
            imageSets.sort(key=int)

            # choose dataset randomly
            # load currently saved data
            with open("CollectedData/userData.json", "r") as JSONfile:
                logs = json.load(JSONfile)
                userLogs = logs.get(uid,{})
                dataSets = userLogs.get("dataSets",{})

            images = []
            clipFeatures = {}
            if(len(dataSets) < len(imageSets)):
                chosenFolder = imageSets[len(dataSets)]

                for file_name in os.listdir("./Data/" + chosenFolder + "/"):
                    if file_name.endswith('.jpg'):
                        images.append(file_name)
                
                # store clip data
                with open("./Data/" + chosenFolder + "/CLIPFeatures.csv", "r") as clipFile:
                    reader = csv.reader(clipFile, delimiter=';')
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
            
            with open("CollectedData/userData.json", "w") as JSONfile:
                JSONfile.write(logsStr)

            # load board config from config file
            configData = []
            with open("config.txt", "r") as configFile:
                reader = csv.reader(configFile, delimiter=';')
                for row in reader:
                    configData.append({"ord": row[1], "size": int(row[0])})

            targetImage = ""
            sorted_images = np.array(images)
            if (chosenFolder != "END"):
                # same image for each dataset
                with open("./Data/" + chosenFolder + "/chosenTarget.txt", "r") as targetFile:
                    targetImage = targetFile.readline()  

                # Convert the map's arrays from strings to floats
                float_map = {k: np.array(list(map(float, v))) for k, v in clipFeatures.items()}

                # Collect all float arrays into a single NumPy array
                X = np.array(list(float_map.values()))
                # Assuming you need a 2D array (for example purposes)
                X = X.reshape(len(images), -1).astype(np.float32)

                imagesOnRow = configData[(int(uid) + int(iteration)) % len(configData)]['size']

                _, sorted_images = selfSort.sort_with_flas(X.copy(), images, nc=49, n_images_per_site=imagesOnRow, radius_factor=0.7, wrap=False)

            # send dataset and list of contents back to JS
            self.send_response(200) 
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            response = {'images': images, 'folder' : chosenFolder, 'boardsConfig' : configData, 'target' : targetImage, 'ss_images' : sorted_images.tolist()}
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
            with open("CollectedData/userData.json", "r") as JSONfile:
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
            
            with open("CollectedData/userData.json", "w") as JSONfile:
                JSONfile.write(logsStr)
            self.send_response(200) 


        ############### Track scrollbar position ###############
        elif self.path.startswith('/scrollPositions'):
            # load received JSON data
            contentLength = int(self.headers.get('content-length'))
            decodedData = self.rfile.read(contentLength).decode()
            logJSON = json.loads(decodedData)

            # convert to csv
            toLogText = str(uid)+";"+str(iteration)+";"+str(logJSON["timestamp"])+";"+str(logJSON["scrollPos"])+";"+str(logJSON["totalScroll"])+";"+str(logJSON["windowW"])+";"+str(logJSON["windowH"])+";"+str(logJSON["navbarH"])+";"+str(logJSON["firstRowStart"])+";"+str(logJSON["secondRowStart"])+";"+str(logJSON["imageHeight"])+";"+str(logJSON["missedTarget"])+"\n"

            # write csv data to disk
            with open("CollectedData/scrollPositions.txt", 'a') as csvFile:
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
            with open("CollectedData/submissions.txt", 'a') as csvFile:
                csvFile.write(toLogText)
            self.send_response(200)


        # general send response
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        return




if __name__ == '__main__':
    http.server.test(TrackingServer, http.server.HTTPServer, port=8001)