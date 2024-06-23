#!/usr/bin/env python3

import json, http.server, os, random
from urllib.parse import urlparse, parse_qs

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
            newUid = 0
            try:
                with open("CollectedData/userData.json", "r") as fh:
                    logs = json.load(fh)
                    newUid = max(map(int, logs.keys())) + 1     # gets last known user and increments its ID
            except json.JSONDecodeError:  # file empty
                logs = {}

            # store new user to .json
            logs[str(newUid)] = {}
            logsStr = json.dumps(logs, indent=4)
            
            with open("CollectedData/userData.json", "w") as JSONfile:
                JSONfile.write(logsStr)

            # send new user ID to JS
            self.send_response(200) 
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            response = {'new_id': newUid}
            self.wfile.write(json.dumps(response).encode('utf-8'))

            return
        

        ############### Get images in a folder ###############
        elif self.path.startswith('/getImages'):    
            imageSets = [folder for folder in os.listdir("./Data/")]

            # choose dataset randomly
            chosenFolder = random.choice(imageSets)
            images = []
            for file_name in os.listdir("./Data/" + chosenFolder + "/"):
                if file_name.endswith('.jpg'):
                    images.append(file_name)

            # send dataset and list of contents back to JS
            self.send_response(200) 
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            response = {'images': images, 'folder' : chosenFolder}
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