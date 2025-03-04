import $ from 'jquery';
import 'jquery.waitforimages';

const service_server = "" 

// start javascript after page loads
$(document).ready(function () {
    console.log("Test");
    // setup image compare overlay
    let imageCompare = $("#image-compare");
    imageCompare.click(function () {
        imageCompare.fadeOut("fast", function () { imageCompare.empty(); });
        toggleScroll();
        storeSubmissionAttempt(UserID, currentIteration, "COM_CLOSE", 3);
    });
    imageCompare.fadeOut();

    // setup results overlay
    hideResult("setup");

    // setup target image overlay
    let targetImageDiv = $('#targetImageDiv');
    targetImageDiv.click(function () {
        toggleTargetAndStartTracker();
    });

    // setup end overlay
    $('#end-overlay').fadeOut();

    // start by showing overlay with info
    showStartOverlay();

});

document.addEventListener("DOMContentLoaded", () => {
    const start_button = document.querySelector("#start-btn");
    start_button.addEventListener("click", () => {
        firstRunLoad();
    });

    const toggle_button = document.querySelector("#solution-button");
    toggle_button.addEventListener("click", () => {
        toggleSolutionDisplay();
    });

    const target_button = document.querySelector("#target-button");
    target_button.addEventListener("click", () => {
        toggleTargetButton();
    });

    const new_user_button = document.querySelector("#new-user-button");
    new_user_button.addEventListener("click", () => {
        startWithNewUser();
    });

    const full_screen_button = document.querySelector("#full-screen-button");
    full_screen_button.addEventListener("click", () => {
        toggleFullScreen();
    });

    const current_iteration_button = document.querySelector("#current-iteration-button");
    current_iteration_button.addEventListener("click", () => {
        skipCurrentIteration();
    });

});

async function firstRunLoad() {
    // hide instruction overlay
    hideStartOverlay();
  

    const params = new URLSearchParams(window.location.search);
    const prolificPID = params.get('PROLIFIC_PID');
    const studyID = params.get('STUDY_ID') || '';
    const sessionID = params.get('SESSION_ID') || '';
    
    // If PROLIFIC_PID is missing, redirect to inputPID.html
    if (!prolificPID) {
        //window.location.replace('inputPID.html');
        console.log("NO PROLIFIC PID, ABORT");
        return;
    }


    
    let request_body = JSON.stringify({ 'prolificPID': prolificPID, 'studyID': studyID, 'sessionID': sessionID });
        // load existing user (and his progress)
        loadOldUser(request_body).then(result => {
            if (result['loadFailed'] == 1) {
                createNewUser(request_body).then(result => {
                    setupAdminMode(result.adminMode);
                    loadNextIteration();
                });
            } else {
                setupAdminMode(result.adminMode);
                loadOldIteration(result);
            }
        });
    }
    
    
    //=============== New user creation (first iteration) ===============//
    
    let UserID = -1;
    let currentIteration = -1;
    let totalNumberOfSets = -1;
    let adminEnabled = false;

async function createNewUser(request_body) {
    let response = await fetch(service_server + "/api/newUser", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: request_body,
      });

      if (response.ok){
        let data = await response.json();
        data = JSON.parse(data)
        UserID = data.new_id;       // receive next user ID
        totalNumberOfSets = data.numOfSets;
        localStorage.setItem('LastUserID', UserID);
        return data;
      }
      else{
        console.error('There was a problem with a fetch operation:');
      }
}


//alternative load old user
async function loadOldUser(request_body) {
    
    let response = await fetch(service_server + "/api/" + "oldUser", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: request_body,
      });
      
        //uid=" + UserID + "&iteration=" + currentIteration
      if (response.ok){
        
        let data = await response.json();
        data = JSON.parse(data)
        return data;
      }
      else{
        console.error('There was a problem with a fetch operation:');
      }


}


// Enable admin features if requested
function setupAdminMode(adminMode) {
    if (adminMode != true) {
        $('#solutionButton').remove();
        $('#newUserButton').remove();
    } else {
        console.log("Admin mode enabled!");
        adminEnabled = adminMode;
    }
}


//=============== Enable / disable scrolling ===============//

function toggleScroll() {
    const body = document.body;

    if (body.style.overflow === 'hidden') {
        body.style.overflow = ''; // Re-enable scrolling
    } else {
        body.style.overflow = 'hidden'; // Disable scrolling
    }
}


//=============== Scroll tracking ===============//

const SCROLL_LOG_INTERVAL = 250;   // how often to log
const SCROLL_BATCH_SIZE = 10;     // how many logs to batch before sending
let scrollTrackerRunning = false;
let trackerIntervalID;

function startScrollTracker() {
    trackerIntervalID = setInterval(() => {
        sendScrollData(UserID, currentIteration);
    }, SCROLL_LOG_INTERVAL);

    scrollTrackerRunning = true;
    storeScrollbarPos(true);    // store initial position (start time as well)
}


function stopScrollTracker() {
    clearInterval(trackerIntervalID);

    scrollTrackerRunning = false;
}

let targetMissed = 0;
let targetWasOnScreen = false;
let scrollPayloads = { 'multipleScrollData': [] };

// store scroll position every time user scrolls
window.addEventListener('scroll', () => {
    if (!scrollTrackerRunning) return;  // only track if tracker is running
    storeScrollbarPos(false);
});

function storeScrollbarPos(afterLoadIndicator) {
    if (targetMissed === 0) {
        const imageToFindSrc = $('#targetImageDiv').find('img').attr('src');
        const targetObjects = $('div.image-container').find('img[src="' + imageToFindSrc + '"]');
        if (targetObjects.length > 0) {
            const targetPos = targetObjects[0].getBoundingClientRect();    // position relative to viewport
            const bottomOfTargetPos = targetPos.bottom;
            const topOfTargetPos = targetPos.top;

            if (bottomOfTargetPos < 0) {
                targetMissed = 1;
            } else if (topOfTargetPos < window.innerHeight) {    // on screen
                targetWasOnScreen = true;
            } else if (targetWasOnScreen && topOfTargetPos >= window.innerHeight) {  // already was on screen but then user scrolled up again
                targetMissed = 1;
            }
        }
    }

    let afterLoad = 0;
    if (afterLoadIndicator) {
        afterLoad = 1;
    }

    let firstRowImage = $('#imageGrid > div:nth-child(1)')[0];
    let secondRowImage = $('#imageGrid > div:nth-child(' + (selectedNumPerRow + 1) + ')')[0];

    let payload = {
        "timestamp": Date.now(),
        "scrollPos": document.documentElement.scrollTop,
        "totalScroll": document.documentElement.scrollHeight,
        "windowW": window.innerWidth,
        "windowH": window.innerHeight,
        "navbarH": document.getElementsByClassName("navbar")[0].clientHeight,
        "firstRowStart": firstRowImage.offsetTop,
        "secondRowStart": secondRowImage.offsetTop,
        "imageHeight": firstRowImage.offsetHeight,
        "missedTarget": targetMissed,
        "afterLoad": afterLoad
    };

    scrollPayloads['multipleScrollData'].push(payload);
}



async function sendScrollData(uid, iteration) {
    let request_body = JSON.stringify({
        "uid": UserID,
        "iteration": currentIteration,
        "log": JSON.stringify(scrollPayloads)
      });
    let response = await fetch(service_server + "/api/" + "scrollPositions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: request_body,
      });
      
        //uid=" + UserID + "&iteration=" + currentIteration
      if (response.ok){
        
        let data = await response.json();
        data = JSON.parse(data)
        scrollPayloads['multipleScrollData'] = [];
      }
      else{
        console.error('There was a problem with a fetch operation:', error);
      }


}

//=============== Load new iteration of images ===============//
let selectedNumPerRow = 4;

function loadNextIteration() {
    currentIteration += 1;
    updateProgress();

    targetMissed = 0;
    targetWasOnScreen = false;

    // empty everything that will be reloaded
    $('#cursorCheckbox').prop('checked', false);
    $('#imageGrid').empty();
    $('#targetImageDiv').empty();

    // load everything
    getImageList().then(response => {

        if (response['folder'] == "END") return Promise.reject('END_OF_TEST');

        const imageFilenames = response['dataSet'];

        const ssImageFilenames = response['ssDataSet'];

        const imageToFind = response['target'];          // always same target image for each dataset

        selectedNumPerRow = response['boardSize'];

        let boardOrdering = response['sortingMethod'];

        // if 16 images => attention check => force board config
        if (imageFilenames.length <= 16) {
            selectedNumPerRow = 4;      // force 4 per row
            boardOrdering = "sp";       // force side panel ordering
        }

        const orderingName = orderImages(imageFilenames, boardOrdering, ssImageFilenames, selectedNumPerRow);

        setupCurrentIteration(imageFilenames, imageToFind, response['folder'], orderingName);
        return { "target": imageToFind, "allImages": imageFilenames, "dataset": response['folder'], "ordering": orderingName, "perRow": selectedNumPerRow }

    }).then(result => storeImageConfig(UserID, currentIteration, result["target"], result["allImages"], result["dataset"], result["ordering"], result["perRow"])).then(result => {

        
        return $('#imageGrid').waitForImages(function () {      // wait for images to load before starting tracker
            // actions after images load
            
            if (!gameEnded) {
                document.documentElement.scrollTop = 0;
                toggleLoadingScreen(true);      // true = also toggle scroll

                toggleTargetImage();
            }
        }); 
    }).catch(error => {
        if (error === 'END_OF_TEST') {
            endTesting();
        }
    });
}

// load already ongoing iteration
function loadOldIteration(currIterData) {
    UserID = parseInt(currIterData['userID']);
    currentIteration = parseInt(currIterData['currIter']);
    updateProgress();

    targetMissed = 0;
    targetWasOnScreen = false;

    // empty everything that will be reloaded
    $('#cursorCheckbox').prop('checked', false);
    $('#imageGrid').empty();
    $('#targetImageDiv').empty();

    // setup everything
    if (currIterData['currDataFolder'] == "END") return endTesting(false);

    const imageFilenames = currIterData['currImages'];
    const imageToFind = currIterData['currTarget'];
    selectedNumPerRow = parseInt(currIterData['currBoardSize']);
    const orderingName = currIterData['currOrdering'];

    setupCurrentIteration(imageFilenames, imageToFind, currIterData['currDataFolder'], orderingName);


    return $('#imageGrid').waitForImages(function () {      // wait for images to load before starting tracker
        // actions after images load

        if (!gameEnded) {
            document.documentElement.scrollTop = 0;
            toggleLoadingScreen(true);      // true = also toggle scroll

            toggleTargetImage();
        }
    });
}


async function getImageList() {
    let request_body = JSON.stringify({
        "uid": UserID,
        "iteration": currentIteration
      });
    let response = await fetch(service_server + "/api/" + "getImages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: request_body,
      });
      
        //uid=" + UserID + "&iteration=" + currentIteration
      if (response.ok){
        
        let data = await response.json();
        data = JSON.parse(data)
        const dataSet = data.images;
        const folder = data.folder;
        const ssDataSet = data.ss_images;
        return { "dataSet": dataSet, "folder": folder, 'boardSize': data.boardSize, 'sortingMethod' : data.sortingMethod, 'target': data.target, "ssDataSet": ssDataSet };  
      }
      else{
        console.error('There was a problem with a fetch operation:', error);
      }
}


// setup current board with supplied data
function setupCurrentIteration(imageFilenames, imageToFind, dataFolder, orderingName) {
    if (orderingName === "side-panel") {
        displaySidePanel();
    } else {
        hideSidePanel();
    }

    $('#imageGrid').css('grid-template-columns', 'repeat(' + selectedNumPerRow + ', 1fr)');
    let lastEmpty = false;
    const imageGrid = $('#imageGrid');
    imageFilenames.forEach(function (filename) {
        if (filename === "empty") {     // empty image
            imageGrid.append($('<div>', { class: 'image-container empty' }));
            imageGrid.append($('<div>', { class: 'empty' }));
            lastEmpty = true;
        } else {
            if (lastEmpty) {    // add separator between videos
                imageGrid.append($('<div>', { class: 'row-separator' }));
                lastEmpty = false;
            }

            imageGrid.append(
                $('<div>', { class: 'image-container' }).append(
                    adminEnabled ? $('<div>', { class: 'adminOverlayText'}).html(parseInt(filename.split("_")[0], 10) + "<br>vID: " + filename.split("_")[2].slice(0, -4)) : null, // add overlay text if in admin mode (from video id remove .jpg)
                    $('<img>', { src: 'Data/' + dataFolder + '/' + filename, class: 'image-item', draggable: 'false', click: handleCompareClick }),
                    $('<div>', { class: 'hover-buttons' }).append(
                        $('<button>', { class: 'btn btn-success', text: 'Submit', click: handleSubmitClick })
                    )
                )
            );
        }
    });

    const targetImageDiv = $('#targetImageDiv');
    targetImageDiv.hide();

    targetImageDiv.append($('<img>', { src: 'Data/' + dataFolder + '/' + imageToFind, class: 'target-image img-fluid', draggable: 'false' }));
}



//=============== Store current image grid info ===============//



async function storeImageConfig(uid, iteration, target, allImages, dataSetNum, orderingName, numPerRow) {
    let payload = JSON.stringify({
        "positions": JSON.stringify(allImages.map(image => ({ "image": image }))),
        "target": target,
        "dataSet": dataSetNum,
        "ordering": orderingName,
        "perRow": numPerRow,
        "uid": uid,
        "iteration": iteration
    });
    let response = await fetch(service_server + "/api/" + "imageConfig", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: payload,
      });
      
        //uid=" + UserID + "&iteration=" + currentIteration
      if (response.ok){
        
        let data = await response.json();
        data = JSON.parse(data);
        return data;
      }
      else{
        console.error('There was a problem with a fetch operation:', error);
      }
}



//=============== Ordering implementations ===============//

function orderImages(imageArray, ordering, ssImageArray, imagesPerRow) {
    let orderingName = "default";
    hideSidePanel();

    switch (ordering) {
        case "ss":
            selfSort(imageArray, ssImageArray);       // self sorting array
            orderingName = "self-sorting";
            break;
        case "mc":
            middleSort(imageArray, imagesPerRow);   // default with middle column filled first
            orderingName = "middle-column";
            break;
        case "r":
            shuffleArray(imageArray);   // random ordering
            orderingName = "random";
            break;
        case "sp":
            orderingName = "side-panel";
            break;
        case "lab":
            selfSort(imageArray, ssImageArray);       // self sorting array (using LAB colors)
            orderingName = "LAB-self-sorting";
            break;
        case "group":
            groupSort(imageArray, imagesPerRow);   // group sorting
            orderingName = "group-video";
            break;
        default:
            break;      // default order on invalid value
    }

    return orderingName;
}


// Fisher–Yates shuffle (random)
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        // Generate a random index between 0 and i (inclusive)
        const randomIndex = Math.floor(Math.random() * (i + 1));

        // Swap elements array[i] and array[randomIndex]
        [array[i], array[randomIndex]] = [array[randomIndex], array[i]];
    }
}

// self-sorting array algorithm
function selfSort(imageArray, ssImageArray) {
    imageArray.length = 0;
    imageArray.push(...ssImageArray);     // already comes sorted from python server - no change needed
}

// group sorting algorithm - each image filename can be split using '_', the last part is used for grouping (video id). Pads with empty images to fill in row (each group starts on a new row then). Groups are then ordered by the lowest first part of filename in that group (lower number = first)
function groupSort(imageArray, imagesPerRow) {

    // Step 1: Create a map of groups, where the key is the group id and value is an array of image objects with rank and name
    let groupMap = {};

    imageArray.forEach(imageName => {
        const parts = imageName.split('_');
        const rank = parseInt(parts[0], 10); // Rank is the first part
        const vidTime = parseInt(parts[1], 10);
        const groupId = parts[2];            // Group ID is the third part (here with .jpg -> fine to use)

        // Create an entry for the group if it doesn't exist yet
        if (!groupMap[groupId]) {
            groupMap[groupId] = [];
        }

        // Add the image to the group array
        groupMap[groupId].push({ name: imageName, rank: rank, vidTime: vidTime });
    });

    // Step 2: Sort each group by video time, then sort the groups by the lowest rank in each group
    const sortedGroups = Object.keys(groupMap)
        .map(groupId => {
            // Sort images inside the group by video time
            groupMap[groupId].sort((a, b) => a.vidTime - b.vidTime);

            // Find the lowest rank in the group
            const lowestRank = Math.min(...groupMap[groupId].map(image => image.rank));

            // Add "empty" images to fill the last row if necessary
            const totalImages = groupMap[groupId].length;
            const remainder = totalImages % imagesPerRow;
            if (remainder !== 0) {
                const emptyImagesNeeded = imagesPerRow - remainder;
                // Add "empty" images at the end of the group
                for (let i = 0; i < emptyImagesNeeded; i++) {
                    groupMap[groupId].push({ name: "empty", rank: Infinity, vidTime: Infinity });
                }
            }

            return {
                groupId: groupId,
                images: groupMap[groupId],
                lowestRank: lowestRank  // Store the lowest rank for sorting groups
            };
        })
        .sort((a, b) => a.lowestRank - b.lowestRank);  // Sort groups by the lowest rank in each group

    // Step 3: Flatten the sorted groups into a single array of image names
    const sortedImageArray = sortedGroups.flatMap(group => group.images.map(image => image.name));

    // replace array
    imageArray.length = 0;
    imageArray.push(...sortedImageArray);
}

// middle-column first sorting algorithm
function middleSort(imageArray, imagesPerRow) {

    const numRows = Math.ceil(imageArray.length / imagesPerRow);

    const sortedArray = new Array(imageArray.length).fill(undefined);   // empty array

    // calculate the middle columns indices
    const middleLeft = Math.floor(imagesPerRow / 2) - Math.floor(imagesPerRow / 4);
    const middleRight = Math.ceil(imagesPerRow / 2) + Math.max((Math.floor(imagesPerRow / 4) - 1), 0);

    // extract items for middle columns
    let currentImageIndex = 0;
    for (let row = 0; row < numRows; row++) {
        const middleLeftIndex = row * imagesPerRow + middleLeft;
        const middleRightIndex = row * imagesPerRow + middleRight;

        for (let i = middleLeftIndex; i <= middleRightIndex; i++) {
            sortedArray[i] = imageArray[currentImageIndex];
            currentImageIndex++;
        }
    }

    // fill remaining spots with the rest of the items
    const emptyIndices = sortedArray.map((item, index) => item === undefined ? index : null).filter(index => index !== null);
    for (const index of emptyIndices) {
        sortedArray[index] = imageArray[currentImageIndex];
        currentImageIndex++;
    }

    // replace array
    imageArray.length = 0;
    imageArray.push(...sortedArray);
}

function euclideanDistance(a, b) {
    return Math.sqrt(a.reduce((sum, value, index) => sum + Math.pow(value - b[index], 2), 0));
}

// find sum of an array
function computeSum(arr) {
    return arr.reduce((acc, val) => acc + parseFloat(val), 0);  // adds up all values in an array
}

function displaySidePanel() {
    const sidePanel = $('#sidePanel');
    sidePanel.show();

    const imageGrid = $('#imageGrid');
    imageGrid.css('margin-left', '15%');
}

function hideSidePanel() {
    const sidePanel = $('#sidePanel');
    sidePanel.hide();

    const imageGrid = $('#imageGrid');
    imageGrid.css('margin-left', '0%');
}


//=============== Submitting an image ===============//

function handleSubmitClick(event) {
    // Find the img element within the same .image-container as the clicked button
    const clickedImageContrainer = $(event.target).closest('.image-container');
    const clickedImage = clickedImageContrainer.find('img');
    const imgSrc = clickedImage.attr('src');
    // Extract the last part of the src URL after the last '/'
    const imageName = imgSrc.substring(imgSrc.lastIndexOf('/') + 1);

    const imageToFindSrc = $('#targetImageDiv').find('img').attr('src');
    const targetImageName = imageToFindSrc.substring(imageToFindSrc.lastIndexOf('/') + 1);

    if (imageName === targetImageName) {
        storeSubmissionAttempt(UserID, currentIteration, imageName, 1);
        storeScrollbarPos(false);   // store last scroll position
        stopScrollTracker();
        sendScrollData(UserID, currentIteration);   // send any remaining scroll data
        showResult("correct");
        hideSkipButton();       // hide skip button if it was visible

        setTimeout(function () {
            hideResult("correct");
            toggleLoadingScreen(false);
            loadNextIteration();
        }, 1000);
    } else {
        storeSubmissionAttempt(UserID, currentIteration, imageName, 0);
        shakeImage(clickedImage);

        showResult("fail");
        setTimeout(function () {
            hideResult("fail");
        }, 1500);
    }

}


// store any submission attempt
async function storeSubmissionAttempt(uid, iteration, image, correct) {

    let firstRowImage = $('#imageGrid > div:nth-child(1)')[0];
    let secondRowImage = $('#imageGrid > div:nth-child(' + (selectedNumPerRow + 1) + ')')[0];
    let request_body = JSON.stringify({
        "uid": UserID,
        "iteration": currentIteration,
        "timestamp": Date.now(),
        "scrollPos": document.documentElement.scrollTop,
        "totalScroll": document.documentElement.scrollHeight,
        "navbarH": document.getElementsByClassName("navbar")[0].clientHeight,
        "windowH": window.innerHeight,
        "firstRowStart": firstRowImage.offsetTop,
        "secondRowStart": secondRowImage.offsetTop,
        "imageHeight": firstRowImage.offsetHeight,
        "correct": correct,
        "image": image
      });


    let response = await fetch(service_server + "/api/" + "submissions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: request_body,
      });
      
        //uid=" + UserID + "&iteration=" + currentIteration
      if (response.ok){
        
        let data = await response.json();
        data = JSON.parse(data);
        return;
      }
      else{
        console.error('There was a problem with a fetch operation:', error);
      }
}

// shake image on incorrect submission
function shakeImage(image) {
    image.addClass("shake");
    setTimeout(function () {
        image.removeClass("shake");
    }, 500);
}


//=============== Result overlay ===============//

function showResult(result) {

    let resultOverlay = $('#result-overlay');
    resultOverlay.empty();

    if (result === "correct") {
        resultOverlay.append("<div class='correct'>Correct image! Moving to another example...</div>")
    } else if (result === "skip") {
        resultOverlay.append("<div class='skipped'>Example skipped! Moving to another example...</div>")
    } else if (result === "endOfTest") {
        resultOverlay.append("<div class='endOfTest'>Time is up! This marks the end of the test.</div>")
    } else {
        resultOverlay.append("<div class='incorrect'>Incorrect image, try again.</div>")
    }

    resultOverlay.fadeIn();
    toggleScroll();
}

function hideResult(result) {
    let resultOverlay = $('#result-overlay');
    resultOverlay.fadeOut();

    if (result === "fail") {
        toggleScroll();
    }
}

//=============== Progress display ===============//¨

function updateProgress() {
    const progressDisplay = document.getElementById('progress');

    const currDisplayIter = currentIteration + 1;
    progressDisplay.textContent = currDisplayIter + "/" + totalNumberOfSets;
}

//=============== Start of test (overlay) ===============//

function showStartOverlay() {
    let startOverlay = $('#start-overlay');
    startOverlay.fadeIn();

    const body = document.body;
    body.style.overflow = 'hidden';
}

function hideStartOverlay() {
    let startOverlay = $('#start-overlay');
    startOverlay.fadeOut();
    startOverlay.empty();
}

//=============== End of test (overlay) ===============//

let gameEnded = false;

function endTesting(payProlific = true) {
    stopScrollTracker();
    $('#end-overlay').css('background-color', 'black');
    showEndOverlay();
    gameEnded = true;

    if (payProlific) {
        // If Prolific URL is set, redirect there after 5 seconds
        redirectCompletionProlific();
    }
}

function showEndOverlay() {
    let endOverlay = $('#end-overlay');

    endOverlay.empty();
    endOverlay.append("<div class='endOfTest'>All tasks done! This marks the end of the test. You'll be shortly redirected back to Prolific.</div><br>");
    if (adminEnabled) {    // hide new user button for standard users
        endOverlay.append('<button type="button" class="btn btn-primary end-btn" onclick="startWithNewUser()">Go again (new user)</button>');
    }
    endOverlay.fadeIn();

    const body = document.body;
    body.style.overflow = 'hidden';
}

function hideEndOverlay() {
    let endOverlay = $('#end-overlay');
    endOverlay.fadeOut();
    endOverlay.empty();
}

function redirectCompletionProlific() {
    const redirectProlificURL = null; //e.g. "https://app.prolific.co/submissions/complete?cc=";

    if (redirectProlificURL) {
        setTimeout(function () {
            window.location.replace(redirectProlificURL);
        }, 5000);
    } else {
        console.log("No Prolific redirect URL set.");
    }
}


//=============== Start over (new user) ===============//

function startWithNewUser() {
    // Remove parameters from URL
    const cleanUrl = window.location.origin + window.location.pathname;
    // Refresh the page
    window.location.replace(cleanUrl);
}


//=============== Loading overlay ===============//

function toggleLoadingScreen(boolScroll) {
    const loadingScreen = $('#loading-screen');

    loadingScreen.fadeToggle('slow');
    if (boolScroll) {
        toggleScroll();
    }
}


//=============== Target image overlay ===============//

function toggleTargetImage() {
    const targetImageDiv = $('#targetImageDiv');

    if (scrollTrackerRunning) { // skip first close
        if (targetImageDiv.is(':visible')) {
            storeSubmissionAttempt(UserID, currentIteration, "TAR_CLOSE", 6);
        } else {
            storeSubmissionAttempt(UserID, currentIteration, "TAR_OPEN", 5);
        }
    }

    targetImageDiv.fadeToggle();
    toggleScroll();
}

function toggleTargetButton() {
    toggleTargetAndStartTracker();
}

function toggleTargetAndStartTracker() {
    toggleTargetImage();
    if (!scrollTrackerRunning) {
        startScrollTracker();   // start tracker on close
        startSkipTimer();
    }
}

// Spacebar to toggle target image
document.addEventListener('keydown', function (event) {
    if (event.key === ' ') {
        // Prevent the default spacebar action (scrolling)
        event.preventDefault();

        // Active only when button can be pressed as well (not on loading screen)
        if (scrollTrackerRunning) {
            toggleTargetImage();
        }
    }
});


//=============== Image compare overlay ===============//

function handleCompareClick(event) {
    let clonedImage = $(event.target).closest('.image-container').find('img').clone();
    let clonedTarget = $('#targetImageDiv').find('img').clone();

    let compareOverlay = $('#image-compare');
    compareOverlay.append(clonedImage);
    compareOverlay.append(clonedTarget);

    compareOverlay.fadeIn();
    toggleScroll();

    const clonedImageSrc = clonedImage.attr('src');
    storeSubmissionAttempt(UserID, currentIteration, clonedImageSrc.substring(clonedImageSrc.lastIndexOf('/') + 1), 2);    // track compare usage
}


//=============== Display solution checkmark ===============//

function toggleSolutionDisplay() {
    const imageToFindSrc = $('#targetImageDiv').find('img').attr('src');

    const desiredImage = $('div.image-container').find('img[src="' + imageToFindSrc + '"]');

    if (desiredImage.length > 0) {
        const windowHeight = $(window).height();
        const imageTopOffset = desiredImage.offset().top;
        const scrollPosition = imageTopOffset - (windowHeight / 2) + (desiredImage.height() / 2);

        if (!desiredImage.hasClass('shining')) {
            $('html, body').animate({
                scrollTop: scrollPosition
            }, 0); // Adjust the duration as needed
        }


        desiredImage.toggleClass('shining');
    }
}


//=============== Fullscreen button ===============//

function toggleFullScreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch((e) => {
            alert('Error attempting to enable full-screen mode: ' + e.message);
        });
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}

//=============== Skip button ===============//

function skipCurrentIteration() {
    storeSubmissionAttempt(UserID, currentIteration, "SKIP", 4);
    storeScrollbarPos(false);   // store last scroll position
    stopScrollTracker();
    showResult("skip");
    hideSkipButton();

    setTimeout(function () {
        hideResult("skip");
        toggleLoadingScreen(false);
        loadNextIteration();
    }, 1000);
}

// toggle skip button visibility
function hideSkipButton() {
    $('#skipButton').hide();
    stopSkipTimer();
}

function showSkipButton() {
    $('#skipButton').show();
}

let skipTimerId;
const SKIP_BUTTON_APPEAR_TIME = 30000;  // 30 seconds

function startSkipTimer() {
    if (skipTimerId) {
        clearTimeout(skipTimerId);
    }

    skipTimerId = setTimeout(function () {
        showSkipButton();
    }, SKIP_BUTTON_APPEAR_TIME);  // show after time is up
}

function stopSkipTimer() {
    if (skipTimerId) {
        clearTimeout(skipTimerId);
    }
}