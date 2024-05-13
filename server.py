#!/usr/bin/env python3

import json, http.server, os, random
from urllib.parse import urlparse, parse_qs

class TrackingServer (http.server.SimpleHTTPRequestHandler):

    def do_POST(self):

        query_params = parse_qs(urlparse(self.path).query)

        try:
            uid = str(int(query_params.get("uid", [0])[0]))
            iteration = str(int(query_params.get("iteration", [0])[0]))
        except (KeyError, ValueError) as e:
            # Handle missing parameters or non-integer values
            uid = "0"
            iteration = "0"


        # tracking scrollbar position
        if self.path.startswith('/scrollPositions.txt'):
            length = int(self.headers.get('content-length'))
            dt = self.rfile.read(length).decode()
            logJSON = json.loads(dt)
            logList = logJSON["log"] 
            windowW = logJSON["windowW"]
            windowH = logJSON["windowH"]

            toLogText = ""
            for logRecord in logList:
                toLogText += str(uid)+";"+str(iteration)+";"+str(logRecord["timestamp"])+";"+str(logRecord["scrollPos"])+";"+str(windowW)+";"+str(windowH)+";"+str(logRecord["missedTarget"])+"\n"

            with open("scrollPositions.txt", 'a') as fh:
                fh.write(toLogText)
            self.send_response(200)

        # clicking submit
        if self.path.startswith('/submissions.txt'):
            length = int(self.headers.get('content-length'))
            dt = self.rfile.read(length).decode()
            logJSON = json.loads(dt)
            logList = logJSON["log"] 
            

            # correct: 0 = incorrect, 1 = correct, 2 = skip

            toLogText = ""
            for logRecord in logList:
                toLogText += str(uid)+";"+str(iteration)+";"+str(logRecord["timestamp"])+";"+str(logRecord["scrollPos"])+";"+str(logRecord["correct"])+";"+str(logRecord["image"])+"\n"

            with open("submissions.txt", 'a') as fh:
                fh.write(toLogText)
            self.send_response(200)
        

        # creates a new user
        elif self.path.startswith('/newUser'):        
            newUid = 0
            try:
                with open("userData.json", "r") as fh:
                    logs = json.load(fh)
                    newUid = max(map(int, logs.keys())) + 1
            except json.JSONDecodeError:  # file empty
                logs = {}

            logs[str(newUid)] = {"targets" : {}}
            logsStr = json.dumps(logs, indent=4)
            
            with open("userData.json", "w") as outfile:
                outfile.write(logsStr)
            self.send_response(200) 
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            response = {'new_id': newUid}
            self.wfile.write(json.dumps(response).encode('utf-8'))

            return

        # get images in a folder
        elif self.path.startswith('/getImages'):    
            imageSets = [folder for folder in os.listdir("./Data/")]

            chosenFolder = random.choice(imageSets)
            images = []
            for file_name in os.listdir("./Data/" + chosenFolder + "/"):
                if file_name.endswith('.jpg'):
                    images.append(file_name)

            self.send_response(200) 
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            response = {'images': images, 'folder' : chosenFolder}
            self.wfile.write(json.dumps(response).encode('utf-8'))

            return


        # stores just generated layout of images
        elif self.path.startswith('/imageConfig'):
            length = int(self.headers.get('content-length'))
            dt = self.rfile.read(length).decode()
            jsonPayload = json.loads(dt)
            positions = json.loads(jsonPayload["positions"])
            target = jsonPayload["target"]
            dataSet = jsonPayload["dataSet"]
            ordering = jsonPayload["ordering"]
            
                    
            with open("userData.json", "r") as fh:
                logs = json.load(fh)
                userLogs = logs.get(uid,{})

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
            
            logs[uid] = userLogs
            logsStr = json.dumps(logs, indent=4)
            
            with open("userData.json", "w") as outfile:
                outfile.write(logsStr)
            self.send_response(200) 


        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        return




if __name__ == '__main__':
    http.server.test(TrackingServer, http.server.HTTPServer, port=8001)