function displayTargetImage() {
    const targetImageDiv = $('#targetImageDiv');
    targetImageDiv.fadeToggle();
    toggleScroll();
}


function toggleScroll() {
    const body = document.body;

    if (body.style.overflow === 'hidden') {
        body.style.overflow = ''; // Re-enable scrolling
    } else {
        body.style.overflow = 'hidden'; // Disable scrolling
    }
}

// example implementation: Update time left every minute
setInterval(() => {
    const timeLeftDisplay = document.getElementById('timeLeft');
    let currentTime = parseInt(timeLeftDisplay.textContent);
    if (currentTime > 0) {
        timeLeftDisplay.textContent = currentTime - 1;
    }
}, 60000); // Updates every minute




function storeScrollbarPos(uid, iteration) {
    let logData = [{ "timestamp": Date.now(), "scrollPos": document.documentElement.scrollTop, "missedTarget": 0 }]
    let payload = {
        "uid": uid,
        "iteration": iteration,
        "log": logData,
        "windowW": window.innerWidth,
        "windowH": window.innerHeight - (document.getElementsByClassName("navbar")[0].clientHeight + 16) // account for navbar and its padding
    };

    fetch("scrollPositions.txt?uid=" + uid + "&iteration=" + iteration,
        {
            method: "POST",
            body: JSON.stringify(payload)
        });

}

// button for toggling fullscreen
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
            UserID = data.new_id;
        }).catch(error => {
            console.error('There was a problem with a fetch operation:', error);
        });
}

// loads list of images in a dataset from server
function getImageList() {
    return fetch("getImages",
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
            return { "dataSet": dataSet, "folder": folder };
        }).catch(error => {
            console.error('There was a problem with a fetch operation:', error);
        });
}

const SCROLL_LOG_INTERVAL = 1000;   // every second
let trackerIntervalID;

function startScrollTracker(){
    trackerIntervalID = setInterval(() => {
        storeScrollbarPos(UserID, currentIteration)
    }, SCROLL_LOG_INTERVAL);
}


function stopScrollTracker(){
    clearInterval(trackerIntervalID);
}


function loadNextIteration() {
    currentIteration += 1;

    // empty everything that will be reloaded
    $('#cursorCheckbox').prop('checked', false);
    $('#imageGrid').empty();
    $('#targetImageDiv').empty();

    // load everything
    getImageList().then(response => {

        const imageFilenames = response['dataSet'];

        const selectedOrdering = Math.floor(Math.random() * 2);     // now 0 or 1
        const orderingName = orderImages(imageFilenames, selectedOrdering);


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

        return { "target": imageToFind, "allImages": imageFilenames, "dataset": response['folder'], "ordering" : orderingName }

    }).then(result => storeImageConfig(UserID, currentIteration, result["target"], result["allImages"], result["dataset"], result["ordering"])).then(result => {
        return $('#imageGrid').waitForImages(function () {
            // actions after images load
            toggleLoadingScreen(true);

            startScrollTracker();
        });

    });
}


$(document).ready(function () {
    // setup image compare overlay
    let imageCompare = $("#image-compare");
    imageCompare.click(function () {
        imageCompare.fadeOut("fast", function () { imageCompare.empty(); });
        toggleScroll();
    });
    imageCompare.fadeOut();

    // setup results overlay
    hideResult("setup");

    // setup target image overlay
    let targetImageDiv = $('#targetImageDiv');
    targetImageDiv.click(function () { displayTargetImage(); });

    // load everything
    createNewUser().then(result => { loadNextIteration(); });
});


function storeImageConfig(uid, iteration, target, allImages, dataSetNum, orderingName) {
    let payload = {
        "uid": uid,
        "iteration": iteration,
        "positions": JSON.stringify(allImages.map(image => ({ "image": image }))),
        "target": target,
        "dataSet": dataSetNum,
        "ordering": orderingName
    };

    fetch("imageConfig?uid=" + uid + "&iteration=" + iteration,
        {
            method: "POST",
            body: JSON.stringify(payload)
        });
}


function toggleLoadingScreen(boolScroll) {
    const loadingScreen = $('#loading-screen');

    loadingScreen.fadeToggle('slow');
    if (boolScroll) {
        toggleScroll();
    }
}


function orderImages(imageArray, ordering){
    let orderingName = "default";

    switch (ordering) {
        case 0:
            break;                      // ordering in alphabetical order (folder order)
        case 1:
            shuffleArray(imageArray);   // random ordering
            orderingName = "random";
            break;
        default:
            break;
    }
    
    return orderingName;
}


// Fisher–Yates shuffle
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        // Generate a random index between 0 and i (inclusive)
        const randomIndex = Math.floor(Math.random() * (i + 1));

        // Swap elements array[i] and array[randomIndex]
        [array[i], array[randomIndex]] = [array[randomIndex], array[i]];
    }
}


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

function shakeImage(image) {
    image.addClass("shake");
    setTimeout(function () {
        image.removeClass("shake");
    }, 500);
}

function showResult(result) {

    let resultOverlay = $('#result-overlay');
    resultOverlay.empty();

    if (result === "correct") {
        resultOverlay.append("<div class='correct'>Correct image! Moving to another example...</div>")
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



function storeSubmissionAttempt(uid, iteration, image, correct) {
    let logData = [{ "timestamp": Date.now(), "scrollPos": document.documentElement.scrollTop, "correct": correct, "image": image }]
    let payload = {
        "uid": uid,
        "iteration": iteration,
        "log": logData
    };

    fetch("submissions.txt?uid=" + uid + "&iteration=" + iteration,
        {
            method: "POST",
            body: JSON.stringify(payload)
        });

}


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


function handleCompareClick(event) {
    let clonedImage = $(event.target).closest('.image-container').find('img').clone();
    let clonedTarget = $('#targetImageDiv').find('img').clone();

    let compareOverlay = $('#image-compare');
    compareOverlay.append(clonedImage);
    compareOverlay.append(clonedTarget);

    compareOverlay.fadeIn();
    toggleScroll();
}