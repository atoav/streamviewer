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