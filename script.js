function displayTargetImage() {
    const targetImageDiv = $('#targetImageDiv');
    targetImageDiv.toggle();
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

const SCROLL_LOG_INTERVAL = 1000;




function storeScrollbarPos(uid,iteration){
    let logData = [{"timestamp" : Date.now(), "scrollPos" : document.documentElement.scrollTop, "missedTarget" : 0}]
    let payload = {
      "uid": uid,
      "iteration": iteration,
      "log": logData,
      "windowW" : window.innerWidth,
      "windowH" : window.innerHeight - (document.getElementsByClassName("navbar")[0].clientHeight + 16) // account for navbar and its padding
    };
  
    fetch("scrollPositions.txt?uid="+uid+"&iteration="+iteration,
    {
        method: "POST",
        body: JSON.stringify( payload )
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

function createNewUser(){
    return fetch("newUser",
    {
        method: "POST"
    }).then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error('Network response was not ok.');
    }).then(data => {
        UserID = data.new_id;
    }).catch(error => {
        console.error('There was a problem with the fetch operation:', error);
    });
}


$(document).ready(function () {

    createNewUser().then(result => {


    // TODO: this should be loaded from web-server, below is example data
    const imageFilenames = ['0000_168_3.jpg', '0001_144_2.jpg', '0002_456_2.jpg', '0003_168_2.jpg', '0004_204_2.jpg', '0005_54_2.jpg', '0006_330_2.jpg', '0007_234_2.jpg', '0008_126_2.jpg', '0009_60_1085.jpg', '0010_174_1043.jpg', '0011_322_33.jpg', '0012_102_1082.jpg', '0013_338_33.jpg', '0014_128_141.jpg', '0015_1672_96.jpg', '0016_42_5.jpg', '0017_210_683.jpg', '0018_225_683.jpg', '0019_587_5.jpg', '0020_45_375.jpg', '0021_262_701.jpg', '0022_569_6.jpg', '0023_105_375.jpg', '0024_96_5.jpg', '0025_629_7.jpg', '0026_186_1.jpg', '0027_24_1.jpg', '0028_307_682.jpg', '0029_210_682.jpg', '0030_72_302.jpg', '0031_150_916.jpg', '0032_338_121.jpg', '0033_105_661.jpg', '0034_90_5.jpg', '0035_1852_1079.jpg', '0036_480_307.jpg', '0037_397_682.jpg', '0038_84_156.jpg', '0039_533_1086.jpg', '0040_689_5.jpg', '0041_791_302.jpg', '0042_228_5.jpg', '0043_248_119.jpg', '0044_1950_96.jpg', '0045_397_920.jpg', '0046_210_6.jpg', '0047_929_6.jpg', '0048_60_1.jpg', '0049_150_5.jpg', '0050_428_40.jpg', '0051_432_302.jpg', '0052_617_5.jpg', '0053_285_33.jpg', '0054_375_661.jpg', '0055_435_366.jpg', '0056_1151_302.jpg', '0057_294_1053.jpg', '0058_518_307.jpg', '0059_486_300.jpg', '0060_382_376.jpg', '0061_120_821.jpg', '0062_15_683.jpg', '0063_198_5.jpg', '0064_188_105.jpg', '0065_495_307.jpg', '0066_352_33.jpg', '0067_660_105.jpg', '0068_405_33.jpg', '0069_67_896.jpg', '0070_1860_96.jpg', '0071_172_151.jpg', '0072_554_566.jpg', '0073_2473_673.jpg', '0074_127_683.jpg', '0075_8_28.jpg', '0076_292_907.jpg', '0077_157_1019.jpg', '0078_398_97.jpg', '0079_240_682.jpg', '0080_720_1060.jpg', '0081_960_103.jpg', '0082_2145_103.jpg', '0083_247_683.jpg', '0084_225_586.jpg', '0085_187_896.jpg', '0086_492_1079.jpg', '0087_105_121.jpg', '0088_96_1.jpg', '0089_397_907.jpg', '0090_186_1085.jpg', '0091_435_920.jpg', '0092_225_612.jpg', '0093_315_146.jpg', '0094_12_1048.jpg', '0095_420_683.jpg', '0096_318_301.jpg', '0097_270_121.jpg', '0098_300_33.jpg', '0099_232_96.jpg', '0100_354_1083.jpg', '0101_7_710.jpg', '0102_0_875.jpg', '0103_15_146.jpg', '0104_1079_586.jpg', '0105_845_300.jpg', '0106_492_301.jpg', '0107_1748_23.jpg', '0108_240_151.jpg', '0109_1402_365.jpg', '0110_945_103.jpg', '0111_330_309.jpg', '0112_1035_103.jpg', '0113_1538_43.jpg', '0114_204_4.jpg', '0115_255_661.jpg', '0116_60_683.jpg', '0117_855_103.jpg', '0118_240_141.jpg', '0119_982_103.jpg', '0120_450_151.jpg', '0121_848_846.jpg', '0122_698_105.jpg', '0123_195_661.jpg', '0124_375_956.jpg', '0125_952_1016.jpg', '0126_105_314.jpg', '0127_1665_103.jpg', '0128_180_1025.jpg', '0129_360_920.jpg', '0130_210_824.jpg', '0131_188_141.jpg', '0132_420_681.jpg', '0133_187_542.jpg', '0134_731_1048.jpg', '0135_592_94.jpg', '0136_66_1043.jpg', '0137_1049_586.jpg', '0138_659_859.jpg', '0139_1890_96.jpg', '0140_442_131.jpg', '0141_322_755.jpg', '0142_8_819.jpg', '0143_540_44.jpg', '0144_172_682.jpg', '0145_509_1020.jpg', '0146_1455_43.jpg', '0147_1491_795.jpg', '0148_105_683.jpg', '0149_172_268.jpg', '0150_202_105.jpg', '0151_3255_1071.jpg', '0152_132_301.jpg', '0153_307_989.jpg', '0154_780_1064.jpg', '0155_150_826.jpg', '0156_225_860.jpg', '0157_487_661.jpg', '0158_1058_365.jpg', '0159_509_746.jpg', '0160_90_903.jpg', '0161_66_1042.jpg', '0162_1041_756.jpg', '0163_637_681.jpg', '0164_37_682.jpg', '0165_24_1049.jpg', '0166_98_823.jpg', '0167_345_146.jpg', '0168_1049_877.jpg', '0169_112_267.jpg', '0170_922_103.jpg', '0171_698_95.jpg', '0172_810_103.jpg', '0173_126_300.jpg', '0174_225_950.jpg', '0175_495_1074.jpg', '0176_900_103.jpg', '0177_382_22.jpg', '0178_405_790.jpg', '0179_1379_1017.jpg', '0180_825_103.jpg', '0181_615_40.jpg', '0182_645_105.jpg', '0183_352_918.jpg', '0184_1778_23.jpg', '0185_810_40.jpg', '0186_2212_43.jpg', '0187_495_1071.jpg', '0188_7_684.jpg', '0189_352_881.jpg', '0190_2025_43.jpg', '0191_382_374.jpg', '0192_158_105.jpg', '0193_22_30.jpg', '0194_306_298.jpg', '0195_7_857.jpg', '0196_4620_42.jpg', '0197_720_103.jpg', '0198_142_406.jpg', '0199_165_661.jpg'];

    shuffleArray(imageFilenames);

    const imageGrid = $('#imageGrid');
    imageFilenames.forEach(function (filename) {
        imageGrid.append(
            $('<div>', { class: 'image-container' }).append(
                $('<img>', { src: 'Data/12/' + filename, class: 'image-item', draggable: 'false' }),
                $('<div>', { class: 'hover-buttons' }).append(
                    $('<button>', { class: 'btn btn-success', text: 'Submit', click: handleSubmitClick }),
                    $('<button>', { class: 'btn btn-primary', text: 'Compare', click: function() { alert('Compare clicked'); } })
                )
            )
        );
        
    });

    const imageToFind = imageFilenames[Math.floor(Math.random() * imageFilenames.length)];
    console.log(imageToFind);
    const targetImageDiv = $('#targetImageDiv');
    targetImageDiv.hide();

    targetImageDiv.append($('<img>', { src: 'Data/12/' + imageToFind, class: 'target-image img-fluid', draggable: 'false' }));

    return [imageToFind, imageFilenames]
        
    }).then(imageData => storeImageConfig(UserID, 0, imageData[0], imageData[1])).then(resp => {
        setInterval(() => {
            storeScrollbarPos(UserID,0)
        }, SCROLL_LOG_INTERVAL);
    });
    

    $('#imageGrid').waitForImages(function () {
        alert('All images have loaded.');
        // ... actions after images load
    });
});


function storeImageConfig(uid, iteration, target, allImages){
    let payload = {
      "uid": uid,
      "iteration": iteration,
      "positions": JSON.stringify(allImages.map(image => ({ "image": image }))),
      "target": target
    };
  
    fetch("imageConfig?uid="+uid+"&iteration="+iteration,
    {
        method: "POST",
        body: JSON.stringify( payload )
    });
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
    const imgSrc = $(event.target).closest('.image-container').find('img').attr('src');
    // Extract the last part of the src URL after the last '/'
    const imageName = imgSrc.substring(imgSrc.lastIndexOf('/') + 1);

    const imageToFindSrc = $('#targetImageDiv').find('img').attr('src');
    const targetImageName = imageToFindSrc.substring(imageToFindSrc.lastIndexOf('/') + 1);

    if(imageName === targetImageName){
        storeSubmissionAttempt(UserID,0,imageName, 1);
        alert('Correct image: ' + imageName);
    }else{
        storeSubmissionAttempt(UserID,0,imageName, 0);
        alert('Incorrect image: ' + imageName);
    }
    
}


function storeSubmissionAttempt(uid,iteration,image, correct){
    let logData = [{"timestamp" : Date.now(), "scrollPos" : document.documentElement.scrollTop,"correct" : correct, "image" : image}]
    let payload = {
      "uid": uid,
      "iteration": iteration,
      "log": logData
    };
  
    fetch("submissions.txt?uid="+uid+"&iteration="+iteration,
    {
        method: "POST",
        body: JSON.stringify( payload )
    });
  
}


function toggleSolutionDisplay(){
    const imageToFindSrc = $('#targetImageDiv').find('img').attr('src');

    const desiredImage = $('div.image-container').find('img[src="' + imageToFindSrc + '"]');

    const windowHeight = $(window).height();
    const imageTopOffset = desiredImage.offset().top;
    const scrollPosition = imageTopOffset - (windowHeight / 2) + (desiredImage.height() / 2);

    if(!desiredImage.hasClass('shining')){
        $('html, body').animate({
            scrollTop: scrollPosition
        }, 0); // Adjust the duration as needed
    }


    desiredImage.toggleClass('shining');
}