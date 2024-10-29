// start javascript after page loads
$(document).ready(function () {
    // setup image compare overlay
    let imageCompare = $("#image-compare");
    imageCompare.click(function () {
        imageCompare.fadeOut("fast", function () { imageCompare.empty(); });
        toggleScroll();
        storeSubmissionAttempt(UserID, currentIteration, "CLOSE", 3);
    });
    imageCompare.fadeOut();

    // setup results overlay
    hideResult("setup");

    // setup target image overlay
    let targetImageDiv = $('#targetImageDiv');
    targetImageDiv.click(function () {
        toggleTargetImage();
        if (!scrollTrackerRunning) { startScrollTracker(); } // start tracker on close
    });

    // setup end overlay
    $('#end-overlay').fadeOut();

    // start by showing overlay with info
    showStartOverlay();

});

function firstRunLoad() {
    // hide instruction overlay
    hideStartOverlay();

    // load everything
    let lastUser = localStorage.getItem('LastUserID');
    if (!lastUser) {
        createNewUser().then(result => {
            setupAdminMode(result.adminMode);
            loadNextIteration();
        });
    } else {
        // load existing user (and his progress)
        loadOldUser(lastUser).then(result => {
            if (result['loadFailed'] == 1) {
                createNewUser().then(result => {
                    setupAdminMode(result.adminMode);
                    loadNextIteration();
                });
            } else {
                setupAdminMode(result.adminMode);
                loadOldIteration(result);
            }
        });
    }
}


//=============== New user creation (first iteration) ===============//

let UserID = -1;
let currentIteration = -1;
let totalNumberOfSets = -1;

function createNewUser() {
    return fetch("newUser",
        {
            method: "POST"
        }).then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Network response error.');
        }).then(data => {
            UserID = data.new_id;       // receive next user ID
            totalNumberOfSets = data.numOfSets;
            localStorage.setItem('LastUserID', UserID);
            return data;
        }).catch(error => {
            console.error('There was a problem with a fetch operation:', error);
        });
}

// alternative: load old user
function loadOldUser(oldUserID) {
    UserID = oldUserID;

    return fetch("oldUser",
        {
            method: "POST",
            body: JSON.stringify({ 'oldUserID': oldUserID })
        }).then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Network response error.');
        }).then(data => {
            totalNumberOfSets = data.numOfSets;
            return data;
        }).catch(error => {
            console.error('There was a problem with a fetch operation:', error);
        });
}

// Enable admin features if requested
function setupAdminMode(adminEnabled) {
    if (adminEnabled != true) {
        $('.navbar-nav .nav-item:first').remove();
    } else {
        console.log("Admin mode enabled!");
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

const SCROLL_LOG_INTERVAL = 300;   // how often to log
let scrollTrackerRunning = false;
let trackerIntervalID;

function startScrollTracker() {
    trackerIntervalID = setInterval(() => {
        storeScrollbarPos(UserID, currentIteration)
    }, SCROLL_LOG_INTERVAL);

    scrollTrackerRunning = true;
}


function stopScrollTracker() {
    clearInterval(trackerIntervalID);

    scrollTrackerRunning = false;
}

let targetMissed = 0;
let targetWasOnScreen = false;

function storeScrollbarPos(uid, iteration) {
    if (targetMissed === 0) {
        const imageToFindSrc = $('#targetImageDiv').find('img').attr('src');
        const targetPos = $('div.image-container').find('img[src="' + imageToFindSrc + '"]')[0].getBoundingClientRect();    // position relative to viewport
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
        "missedTarget": targetMissed
    };

    fetch("scrollPositions?uid=" + uid + "&iteration=" + iteration,
        {
            method: "POST",
            body: JSON.stringify(payload)
        });
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

        const currBoardConfig = (UserID + currentIteration) % response['boardsConfig'].length;    // each user starts shifted by 1 than previous

        selectedNumPerRow = response['boardsConfig'][currBoardConfig]["size"];

        const orderingName = orderImages(imageFilenames, response['boardsConfig'][currBoardConfig]["ord"], ssImageFilenames, selectedNumPerRow);

        setupCurrentIteration(imageFilenames, imageToFind, response['folder']);

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
    currentIteration = parseInt(currIterData['currIter']);
    updateProgress();

    targetMissed = 0;
    targetWasOnScreen = false;

    // empty everything that will be reloaded
    $('#cursorCheckbox').prop('checked', false);
    $('#imageGrid').empty();
    $('#targetImageDiv').empty();

    // setup everything
    if (currIterData['currDataFolder'] == "END") return endTesting();

    const imageFilenames = currIterData['currImages'];
    const imageToFind = currIterData['currTarget'];
    selectedNumPerRow = parseInt(currIterData['currBoardSize']);

    setupCurrentIteration(imageFilenames, imageToFind, currIterData['currDataFolder']);


    return $('#imageGrid').waitForImages(function () {      // wait for images to load before starting tracker
        // actions after images load

        if (!gameEnded) {
            document.documentElement.scrollTop = 0;
            toggleLoadingScreen(true);      // true = also toggle scroll

            toggleTargetImage();
        }
    });
}

// load a list of images in a dataset from server
function getImageList() {
    return fetch("getImages?uid=" + UserID + "&iteration=" + currentIteration,
        {
            method: "POST"
        }).then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Network response error.');
        }).then(data => {
            const dataSet = data.images;
            const folder = data.folder;
            const ssDataSet = data.ss_images;
            return { "dataSet": dataSet, "folder": folder, 'boardsConfig': data.boardsConfig, 'target': data.target, "ssDataSet": ssDataSet };
        }).catch(error => {
            console.error('There was a problem with a fetch operation:', error);
        });
}


// setup current board with supplied data
function setupCurrentIteration(imageFilenames, imageToFind, dataFolder) {
    $('#imageGrid').css('grid-template-columns', 'repeat(' + selectedNumPerRow + ', 1fr)');

    const imageGrid = $('#imageGrid');
    imageFilenames.forEach(function (filename) {
        imageGrid.append(
            $('<div>', { class: 'image-container' }).append(
                $('<img>', { src: 'Data/' + dataFolder + '/' + filename, class: 'image-item', draggable: 'false' }),
                $('<div>', { class: 'hover-buttons' }).append(
                    $('<button>', { class: 'btn btn-success', text: 'Submit', click: handleSubmitClick }),
                    $('<button>', { class: 'btn btn-primary', text: 'Compare', click: handleCompareClick })
                )
            )
        );

    });

    const targetImageDiv = $('#targetImageDiv');
    targetImageDiv.hide();

    targetImageDiv.append($('<img>', { src: 'Data/' + dataFolder + '/' + imageToFind, class: 'target-image img-fluid', draggable: 'false' }));
}



//=============== Store current image grid info ===============//

function storeImageConfig(uid, iteration, target, allImages, dataSetNum, orderingName, numPerRow) {
    let payload = {
        "positions": JSON.stringify(allImages.map(image => ({ "image": image }))),
        "target": target,
        "dataSet": dataSetNum,
        "ordering": orderingName,
        "perRow": numPerRow
    };

    return fetch("imageConfig?uid=" + uid + "&iteration=" + iteration,
        {
            method: "POST",
            body: JSON.stringify(payload)
        });
}



//=============== Ordering implementations ===============//

function orderImages(imageArray, ordering, ssImageArray, imagesPerRow) {
    let orderingName = "default";

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
        stopScrollTracker();
        showResult("correct");

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
function storeSubmissionAttempt(uid, iteration, image, correct) {

    let firstRowImage = $('#imageGrid > div:nth-child(1)')[0];
    let secondRowImage = $('#imageGrid > div:nth-child(' + (selectedNumPerRow + 1) + ')')[0];

    let payload = {
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
    };

    fetch("submissions?uid=" + uid + "&iteration=" + iteration,
        {
            method: "POST",
            body: JSON.stringify(payload)
        });
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

function endTesting() {
    stopScrollTracker();
    $('#end-overlay').css('background-color', 'black');
    showEndOverlay();
    gameEnded = true;
}

function showEndOverlay() {
    let endOverlay = $('#end-overlay');

    endOverlay.empty();
    endOverlay.append("<div class='endOfTest'>All tasks done! This marks the end of the test.</div><br>");
    endOverlay.append('<button type="button" class="btn btn-primary end-btn" onclick="startWithNewUser()">Go again (new user)</button>')
    endOverlay.fadeIn();

    const body = document.body;
    body.style.overflow = 'hidden';
}

function hideEndOverlay() {
    let endOverlay = $('#end-overlay');
    endOverlay.fadeOut();
    endOverlay.empty();
}


//=============== Start over (new user) ===============//

function startWithNewUser() {
    stopScrollTracker();
    const loadingScreen = $('#loading-screen');
    loadingScreen.fadeIn();
    hideEndOverlay();
    hideResult("setup");
    const targetImageDiv = $('#targetImageDiv');
    targetImageDiv.fadeOut();
    const compareOverlay = $('#image-compare');
    compareOverlay.fadeOut();
    document.body.style.overflow = 'hidden';

    currentIteration = -1;
    gameEnded = false;

    createNewUser().then(result => { loadNextIteration(); });
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
    targetImageDiv.fadeToggle();
    toggleScroll();
}

function toggleTargetButton() {  // TODO: log opening this overlay
    toggleTargetImage();
    if (!scrollTrackerRunning) { startScrollTracker(); } // start tracker on close
}


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