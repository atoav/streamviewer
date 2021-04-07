var socket = io();
let hasEverRun = false;
var isPlaying = false;
let player = null;



// Extract foobar from the .stream-foobar key of an element
function extractStreamKey(e) {
  for (const c of e.classList){
    if (c.startsWith('stream-')) {
      return c.substring(7);
    }
  }
}

// Get the streamkey from the current page
function getStreamKey() {
    let stream = document.getElementById("stream");
    return extractStreamKey(stream);
}

// Returns true if the key k is in the streamlist
function hasStream(streamlist, k) {
  return streamlist.some(({ key }) => key === k);
}

// Returns the Stream from the streamlist
function getStream(streamlist, k) {
  return streamlist.find(({ key }) => key === k);
}

// Send a message to the server when the socket is established
socket.on('connect', function() {
    let key = getStreamKey()
    socket.emit('join', {"key" : key});
    // Ask about the state of the stream
    socket.emit('stream_info', {"key" : key});
});

// After initial connect, receive a streamlist
socket.on('stream_info', function(data) {
    var stream = JSON.parse(data)
    updateStream(stream, "update");
});

// Send a message to the server when the socket is established
socket.on('disconnect', function() {
    let key = getStreamKey()
    socket.emit('leave', {"key" : key});
});

// Send a leave message to the server before unloading the page
window.onbeforeunload = function(event) {
    let key = getStreamKey()
    socket.emit('leave', {"key" : key});
    console.log("Sent leave message");
};

// After initial connect, receive a streamlist
socket.on('viewercount', function(viewercount) {
    updateViewCount(viewercount);
});

// New streamlist arrives here when webserver gets notivied of an stream addition
socket.on('stream_added', function(data) {
    console.log('Stream ' + data['key'] + ' added.');
    var streamlist = JSON.parse(data["list"])
    let streamkey = getStreamKey();
    if (hasStream(streamlist, streamkey)) {
        let stream = getStream(streamlist, streamkey);
        updateStream(stream, "added");
    }else{
        console.log("..but "+streamkey+" was not in streamlist");
        console.log(streamlist);
    }
});

// New streamlist arrives here when webserver gets notivied of a stream removal
socket.on('stream_removed', function(data) {
    console.log('Stream ' + data['key'] + ' removed.');
    let streamkey = getStreamKey();
    if (streamkey == data['key']) {
        updateStream(streamkey, "removed");
    }
});


// Update the count of viewers
function updateViewCount(viewercount) {
    if (document.getElementById("viewcount") !== null) { 
        let count = viewercount['count'];
        if (count < 1) { 
            console.log("Count would have been "+ count +", set to 1 instead");
            count = 1;
        }
        document.getElementById("viewcount").textContent =  viewercount['count'];
    }
}

// Update the stream when it has been added
function updateStream(stream, what) {
    if (what == "update") {
        console.log("Stream "+stream.key+" updated")
        if (!stream.active) {
            deactivateStream(stream.key);
        }else{
            hasEverRun = true;
        }
    } else if (what == "added") {
        console.log("Stream "+stream.key+" has started");
        hasEverRun = true;
        activateStream(stream);
    }else if (what == "removed") {
        console.log("Stream "+stream+" has stopped");
        deactivateStream(stream);
    }
}


function deactivateStream(streamkey) {
    // Add inactive class to body
    document.body.classList.add("inactive");

    // Pause the player
    if (player !== null) {
        player.pause();
    }

    // Get width and height from player
    var videoPlayer = document.getElementById("stream");
    var w = videoPlayer.offsetWidth;
    var h = videoPlayer.offsetHeight;

    // Remove video player
    if (document.getElementById("stream") !== null) { 
      document.querySelectorAll('#stream').forEach(e => e.remove());
    }

    if (player !== null) {
        player.dispose();
    }

    // Get parent element
    let content = document.getElementsByTagName("content")[0];

    // Create a div
    let div = document.createElement("div");
    div.id = "stream";
    div.classList.add("stream-"+streamkey)
    div.style.height = h+"px";
    div.style.width = w+"px";

    // Add a notice to it
    let h2 = document.createElement("h2");
    if (hasEverRun) {
        h2.textContent = "The stream has ended"
        h2.classList.add("stopped");
        document.body.classList.add("stopped");
    }else{
        h2.textContent = "The stream hasn't started yet (or it doesn't exist)"
        h2.classList.add("not_started");
        document.body.classList.add("not-started");
    }
    h2.id = "no-stream-notice";
    div.appendChild(h2);

    content.prepend(div);
}

function activateStream(stream) {
    if (!isPlaying) {
        document.body.classList.remove("inactive");
        document.body.classList.remove("not-started");
        document.body.classList.remove("stopped");

        // Remove div placeholder
        if (document.getElementById("stream") !== null) { 
          document.querySelectorAll('#stream').forEach(e => e.remove());
        }

        // TODO: Add description, ...
        addPlayer(stream.key);
        player = initializePlayer();
        player.load();
        player.play();

        updateDescription(stream);
    }
}


function updateDescription(stream) {
    if (stream.description !== null && stream.description !== "") {
        let descriptions = document.querySelectorAll('.description');
        if (descriptions.length === 0) {
            buildDescriptionBlock();
        }
        let description = document.querySelectorAll('.description')[0];

        // TODO: handle markdown...?
        description.textContent = stream.description;
    }else{
        // There was formerly a description which is now gone, so destroy description
        document.querySelectorAll('.description').forEach(e => e.remove());
    }
}

function buildDescriptionBlock() {
    let content = document.getElementsByTagName("content")[0];
    let section = document.createElement("section");
    section.classList.add("description");
    content.appendChild(section);
}


// When the window is loaded check for errors
window.onload = function() {
    if (!document.body.classList.contains("inactive")){
        player = initializePlayer();
    }
    // Run this block with a delay
    setTimeout(function() { 
        var videoPlayer = document.getElementById("stream");

        if (!document.body.classList.contains("inactive")){
            // If there is an error try every two seconds if the player now finds the
            // video. Once it is found, remove the interval
            if (videoPlayer.classList.contains("vjs-error")) {
                var intervalId = setInterval(function() { 
                    checkIfStillErrored(intervalId) ;
                }, 2000);
            }

            // Autoplay with delay if possible
            player.play();
        }else{
            deactivateStream(getStreamKey());
        }

    }, 200);
}



function checkIfStillErrored(intervalId) {
    var videoPlayer = document.getElementById("stream");
    if (videoPlayer.classList.contains("vjs-error")) {
        console.log("Stream still errored, trying to reload it");
        player.pause();
        player.load();
    }else{
        console.log("Error seems resolved");
        player.load();
        player.play();
        clearInterval(intervalId);
    }
}


function addPlayer(streamkey) {
    // Get parent element
    let content = document.getElementsByTagName("content")[0];

    // Create player
    let videojs = document.createElement("video-js");
    videojs.id = "stream";
    videojs.classList.add("vjs-default-skin", "stream-"+streamkey, );
    videojs.setAttribute("data-setup", '{"fluid": true, "liveui": true}'); 
    videojs.toggleAttribute('controls'); 

    let source = document.createElement("source");
    source.src = "../hls/"+streamkey+".m3u8";
    source.type = "application/x-mpegURL"

    videojs.prepend(source);
    content.prepend(videojs)
}


function initializePlayer() {
    var player = videojs('stream');
    player.autoplay('any');

    function displayMuteifNeeded(player) {
        if (player.muted()){
            let title = document.querySelector("#page_title");
            if (title.querySelector(".muted") == null) {
                let a = document.createElement("a");
                let img = document.createElement("img");
                img.src = "/static/mute.svg";
                a.classList.add("muted");
                a.onclick = function() { 
                    player.muted(false);
                    displayMuteifNeeded(player);
                };
                a.appendChild(img);
                title.appendChild(a);
            }
        }else{
            let title = document.querySelector("#page_title");
            title.querySelectorAll('.muted').forEach(e => e.remove());
        }
    }

    player.on('play', () => { 
        displayMuteifNeeded(player);
    });

    player.on("volumechange",function(){
        displayMuteifNeeded(player);
    });

    player.on(['waiting', 'pause'], function() {
      isPlaying = false;
    });

    player.on('playing', function() {
      isPlaying = true;
    });

    // player.on('error', () => {
    //     player.createModal('Retrying connection');
    //     if (player.error().code === 4) {
    //         this.player.retryLock = setTimeout(() => {
    //             player.src({
    //                 src: data.url
    //             });
    //             player.load();
    //         }, 2000);
    //     }
    // });

    return player;
}