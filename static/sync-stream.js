var socket = io();

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

// Send a message to the server when the socket is established
socket.on('connect', function() {
    let key = getStreamKey()
    socket.emit('join', {"key" : key});
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
        updateStream("activate", streamkey);
    }
});

// New streamlist arrives here when webserver gets notivied of a stream removal
socket.on('stream_removed', function(data) {
    console.log('Stream ' + data['key'] + ' removed.');
    var streamlist = JSON.parse(data["list"])
    let streamkey = getStreamKey();
    updateStream("deactivate", streamkey);
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
function updateStream(what, streamkey) {

    if (what == "activate") {
        console.log("Stream "+streamkey+" has started");
    }else if (what == "deactivate") {
        console.log("Stream "+streamkey+" has stopped");
    }
}


window.onload = function() {
    setTimeout(function() { 
        var player = document.getElementById("stream");
        if (player.classList.contains("vjs-error")) {
            console.log("Contained Error");
            var intervalId = setInterval(checkIfStillErrored, 2000);
            clearInterval(intervalId);
        }
    }, 1000);
}



function checkIfStillErrored() {
    var player = document.getElementById("stream");
    if (player.classList.contains("vjs-error")) {
        console.log("Still errored");
        location.reload(); 
    }else{
        console.log("Not errored anymore");
    }
}