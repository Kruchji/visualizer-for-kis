#!/usr/bin/env python3

import json, http.server, os, csv, lap, time
from urllib.parse import urlparse, parse_qs

# For sorting
import numpy as np
from scipy.ndimage import uniform_filter1d, convolve1d


################## Self-sorting algorithm ##################

''' Calculates the squared L2 (eucldean) distance using numpy. '''
def squared_l2_distance(q, p):
    
    ps = np.sum(p*p, axis=-1, keepdims=True)    
    qs = np.sum(q*q, axis=-1, keepdims=True)
    distance = ps - 2*np.matmul(p, q.T) + qs.T
    return np.clip(distance, 0, np.inf)

''' Applies a low pass filter to the current map'''
def low_pass_filter(map_image, filter_size_x, filter_size_y, wrap=False):
    
    mode = "wrap" if wrap else "reflect" # nearest
    
    im2 = uniform_filter1d(map_image, filter_size_y, axis=0, mode=mode)  
    im2 = uniform_filter1d(im2, filter_size_x, axis=1, mode=mode)  
    return im2

''' Utility function that takes a position and returns 
a desired number of positions in the given radius'''
def get_positions_in_radius(pos, indices, r, nc, wrap):
    if wrap:
        return get_positions_in_radius_wrapped(pos, indices, r, nc)
    else:
        return get_positions_in_radius_non_wrapped(pos, indices, r, nc)
    
''' Utility function that takes a position and returns 
a desired number of positions in the given radius'''
def get_positions_in_radius_non_wrapped(pos, indices, r, nc):
    
    H, W = indices.shape
    
    x = pos % W 
    y = int(pos/W)
    
    ys = y-r
    ye = y+r+1
    xs = x-r
    xe = x+r+1
    
    # move position so the full radius is inside the images bounds
    if ys < 0:
        ys = 0
        ye = min(2*r + 1, H)
        
    if ye > H:
        ye = H
        ys = max(H - 2*r - 1, 0)
        
    if xs < 0:
        xs = 0
        xe = min(2*r + 1, W)
        
    if xe > W:
        xe = W
        xs = max(W - 2*r - 1, 0)
    
    # concatenate the chosen position to a 1D array
    positions = np.concatenate(indices[ys:ye, xs:xe])
    
    if nc is None:
        return positions
    
    chosen_positions = np.random.choice(positions, min(nc, len(positions)), replace=False)
    
    return chosen_positions

''' Utility function that takes a position and returns 
a desired number of positions in the given radius'''
def get_positions_in_radius_wrapped(pos, extended_grid, r, nc):
    
    H, W = extended_grid.shape
    
    # extended grid shape is H*2, W*2
    H, W = int(H/2), int(W/2)    
    x = pos % W 
    y = int(pos/W)
    
    ys = (y-r + H) % H     
    ye = ys + 2*r + 1 
    xs = (x-r + W) % W 
    xe = xs + 2*r + 1 
    
    # concatenate the chosen position to a 1D array
    positions = np.concatenate(extended_grid[ys:ye, xs:xe])
    
    if nc is None:
        return positions
    
    chosen_positions = np.random.choice(positions, min(nc, len(positions)), replace=False)
    
    return chosen_positions

# Fast Linear Assignment Sorting
def sort_with_flas(X, filepaths, nc, n_images_per_site, radius_factor=0.9, wrap=False, return_time=False):
    
    np.random.seed(7)   # for reproducible sortings
    
    # setup of required variables
    N = np.prod(X.shape[:-1])
    X = X.reshape((n_images_per_site, len(X) // n_images_per_site, -1))
    filepaths = np.array(filepaths)
   
    grid_shape = X.shape[:-1]
    H, W = grid_shape
    
    start_time = time.time()
    
    # assign input vectors to random positions on the grid
    grid = np.random.permutation(X.reshape((N, -1))).reshape((X.shape)).astype(float)
    
    # reshape 2D grid to 1D
    flat_X = X.reshape((N, -1))
    
    # create indices array 
    indices = np.arange(N).reshape(grid_shape)
    
    if wrap:
        # create a extended grid of size (H*2, W*2)
        indices = np.concatenate((indices, indices), axis=1 )
        indices = np.concatenate((indices, indices), axis=0 )
    
    radius_f = max(H, W)/2 - 1 # initial radius
        
    while True:
        # compute filtersize that is smaller than any side of the grid
        radius = int(radius_f)
        filter_size_x = min(W-1, int(2*radius + 1))
        filter_size_y = min(H-1, int(2*radius + 1))
        
        # Filter the map vectors using the actual filter radius
        grid = low_pass_filter(grid, filter_size_x, filter_size_y, wrap=wrap)
        flat_grid = grid.reshape((N, -1))
        
        n_iters = 2 * int(N / nc) + 1
        max_swap_radius = int(round(max(radius, (np.sqrt(nc)-1)/2)))
            
        for i in range(n_iters):
            
            # find random swap candicates in radius of a random position
            random_pos = np.random.choice(N, size=1)
            positions = get_positions_in_radius(random_pos[0], indices, max_swap_radius, nc, wrap=wrap)
            
            # calc C
            pixels = flat_X[positions]
            grid_vecs = flat_grid[positions]
            C = squared_l2_distance(pixels, grid_vecs)
            
            # quantization of distances speeds up assingment solver
            C = (C / C.max() * 2048).astype(int)
            
            # get indices of best assignments 
            _, best_perm_indices, _= lap.lapjv(C)
            
            # assign the input vectors to their new map positions
            flat_X[positions] = pixels[best_perm_indices]
            filepaths[positions] = filepaths[positions][best_perm_indices]
        
         # prepare variables for next iteration
        grid = flat_X.reshape(X.shape)
        
        radius_f *= radius_factor
        # break condition
        if radius_f < 1:
            break
               
    duration = time.time() - start_time
    
    if return_time:
        return grid, filepaths, duration
    
    print(f"Sorted with FLAS in {duration:.3f} seconds") 
    return grid, filepaths



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
                targetImage = images[0]     # same image for each dataset

                # Convert the map's arrays from strings to floats
                float_map = {k: np.array(list(map(float, v))) for k, v in clipFeatures.items()}

                # Collect all float arrays into a single NumPy array
                X = np.array(list(float_map.values()))
                # Assuming you need a 2D array (for example purposes)
                X = X.reshape(len(images), -1).astype(np.float32)

                imagesOnRow = configData[(int(uid) + int(iteration)) % len(configData)]['size']

                _, sorted_images = sort_with_flas(X.copy(), images, nc=49, n_images_per_site=imagesOnRow, radius_factor=0.7, wrap=False)

            # send dataset and list of contents back to JS
            self.send_response(200) 
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            response = {'images': sorted_images.tolist(), 'folder' : chosenFolder, 'clip' : clipFeatures, 'boardsConfig' : configData, 'target' : targetImage}
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