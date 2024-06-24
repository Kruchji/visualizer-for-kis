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

    // load everything
    createNewUser().then(result => { loadNextIteration(); });
});


//=============== New user creation (first iteration) ===============//

let UserID = -1;
let currentIteration = -1;

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
        }).catch(error => {
            console.error('There was a problem with a fetch operation:', error);
        });
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


//=============== Board configs ===============//

const boardsConfig = [{ "ord": "ss", "size": 4 }, { "ord": "ss", "size": 8 }, { "ord": "ss", "size": 8 }];


//=============== Load new iteration of images ===============//
let selectedNumPerRow = 4;

function loadNextIteration() {
    currentIteration += 1;

    targetMissed = 0;
    targetWasOnScreen = false;

    // empty everything that will be reloaded
    $('#cursorCheckbox').prop('checked', false);
    $('#imageGrid').empty();
    $('#targetImageDiv').empty();

    // load everything
    getImageList().then(response => {

        if (response['folder'] == "END") return Promise.reject('END_OF_TEST');

        const clipFeatures = response['clip'];

        const imageFilenames = response['dataSet'];

        const currBoardConfig = (UserID + currentIteration) % boardsConfig.length;    // each user starts shifted by 1 than previous

        const orderingName = orderImages(imageFilenames, boardsConfig[currBoardConfig]["ord"], clipFeatures);

        selectedNumPerRow = boardsConfig[currBoardConfig]["size"];
        $('#imageGrid').css('grid-template-columns', 'repeat(' + selectedNumPerRow + ', 1fr)');

        const imageGrid = $('#imageGrid');
        imageFilenames.forEach(function (filename) {
            imageGrid.append(
                $('<div>', { class: 'image-container' }).append(
                    $('<img>', { src: 'Data/' + response['folder'] + '/' + filename, class: 'image-item', draggable: 'false' }),
                    $('<div>', { class: 'hover-buttons' }).append(
                        $('<button>', { class: 'btn btn-success', text: 'Submit', click: handleSubmitClick }),
                        $('<button>', { class: 'btn btn-primary', text: 'Compare', click: handleCompareClick })
                    )
                )
            );

        });

        const imageToFind = imageFilenames[Math.floor(Math.random() * imageFilenames.length)];
        const targetImageDiv = $('#targetImageDiv');
        targetImageDiv.hide();

        targetImageDiv.append($('<img>', { src: 'Data/' + response['folder'] + '/' + imageToFind, class: 'target-image img-fluid', draggable: 'false' }));

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
            const clipFeatures = data.clip;
            return { "dataSet": dataSet, "folder": folder, "clip": clipFeatures };
        }).catch(error => {
            console.error('There was a problem with a fetch operation:', error);
        });
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

function orderImages(imageArray, ordering, clip) {
    let orderingName = "default";

    switch (ordering) {
        case "ss":
            imageArray = selfSort(imageArray, clip);       // self sorting array
            orderingName = "self-sorting";
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
function selfSort(imageArray, clipFeatures) {

    // mock implementation with sum of clip features
    
    const sortedArray = imageArray.sort((a, b) => {
        const sumA = computeSum(clipFeatures[a]);
        const sumB = computeSum(clipFeatures[b]);
        return sumA - sumB;
    });

    
    return sortedArray;
}

// find sum of an array
function computeSum(arr) {
    return arr.reduce((acc, val) => acc + val, 0);  // adds up all values in an array
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
        }, 2000);
    } else {
        storeSubmissionAttempt(UserID, currentIteration, imageName, 0);
        shakeImage(clickedImage);

        showResult("fail");
        setTimeout(function () {
            hideResult("fail");
        }, 2000);
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
// TODO: add updating of progress display

//=============== End of test (overlay) ===============//

let gameEnded = false;

function endTesting() {         // TODO: call after last test
    stopScrollTracker();
    $('#end-overlay').css('background-color', 'black');
    showEndOverlay();
    gameEnded = true;
}

function showEndOverlay() {
    let endOverlay = $('#end-overlay');

    endOverlay.empty();
    endOverlay.append("<div class='endOfTest'>All tasks done! This marks the end of the test.</div>");
    endOverlay.fadeIn();

    const body = document.body;
    body.style.overflow = 'hidden';
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
    // TODO: track end of compare as well?
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