var socket = io();


// Send a message to the server when the socket is established
socket.on('connect', function() {
    socket.emit('connect_list');
});

// After initial connect, receive a streamlist
socket.on('stream_list', function(data) {
    var streamlist = JSON.parse(data["list"])
    updateStreamList(streamlist);
});

// New streamlist arrives here when webserver gets notivied of an stream addition
socket.on('stream_added', function(data) {
    console.log('Stream ' + data['key'] + ' added.');
    var streamlist = JSON.parse(data["list"])
    updateStreamList(streamlist);
});

// New streamlist arrives here when webserver gets notivied of a stream removal
socket.on('stream_removed', function(data) {
    console.log('Stream ' + data['key'] + ' removed.');
    var streamlist = JSON.parse(data["list"])
    updateStreamList(streamlist);
});


setInterval(function() {
    socket.emit("stream_list");
}, 4000)



// Extract foobar from the .stream-foobar key of an element
function extractStreamKey(e) {
  for (const c of e.classList){
    if (c.startsWith('stream-')) {
      return c.substring(7);
    }
  }
}


// Returns true if the key k is in the streamlist
function hasStream(streamlist, k) {
  return streamlist.some(({ key }) => key === k);
}


// Update the count of streams displayed
function updateStreamCount(streams) {
  let existingStreams = Array.from(streams.querySelectorAll('.active_stream')).map(e => extractStreamKey(e))
  // Update the streamcount in the title
  if (document.getElementById("streamheader") !== null) { 
    document.getElementById("streamheader").textContent = "Active Streams [" + existingStreams.length + "]";
  }
}


// Remove/Add the "no streams" message if the streamcount is zero or > zero
function updateNoStreamsMessage(streams) {
  // Add or remove the notification "There are currently no active streams" based on the streamcount
  let existingStreams = Array.from(streams.querySelectorAll('.active_stream')).map(e => extractStreamKey(e))
  if (existingStreams.length > 0) {
    // If there are streams remove the "no streams"-message
    if (document.getElementById("no-stream-notice") !== null) { 
      document.querySelectorAll('#no-stream-notice').forEach(e => e.remove());
    }
  }else{
    if (document.getElementById("no-stream-notice") !== null) { 
      // Make dead sure the notice doesn't exist yet
      document.querySelectorAll('#no-stream-notice').forEach(e => e.remove());
      // If there are no streams add a message
      let h2 = document.createElement("h2");
      h2.textContent = "There are currently no active streams"
      h2.id = "no-stream-notice";
      streams.appendChild(h2);
    }
  }
}

// Mark inactive streams with the .inactive_stream class (animating it's removal)
// Elements with the class .inactive_stream get removed after the transition is
// over by thecallback added by removeAfterAnimation()
function markInaktiveStreams(active_streams, streamlist) {
  // Mark inactive streams with the .inactive_stream class (animating it's removal)
  active_streams.forEach(e => {
    let key = extractStreamKey(e);
    if (!hasStream(streamlist, key)) {
      // Add a removal class to the stream (so the animation starts playing) 
      e.classList.add('inactive_stream');
    }
  });
}

// Add new streams to the ul #streamlist
function addNewStreams(streams, streamlist) {
  // Add all streams from the streamlist that dont exist yet
  let existingStreams = [...streams.querySelectorAll('.active_stream')].map(e => extractStreamKey(e))
  for (const stream of streamlist) {
    if (!existingStreams.includes(stream.key)) {
      // console.log("Streamlist had key "+stream.key+" so it was added");
      let li = document.createElement("li");
      li.classList.add("active_stream");
      li.classList.add("stream-"+stream.key);
      // TODO: Add password and description classes
      let a = document.createElement("a");
      a.href = "streams/"+stream.key;
      a.textContent = stream.key;
      li.appendChild(a);
      streams.appendChild(li);
    }
  }
}

function updateViewcounts(streams, streamlist) {
  let active_streams = streams.querySelectorAll('.active_stream');
  for (const li of active_streams) {
    let key = extractStreamKey(li);
    let match = streamlist.find(stream => stream.key === key);
    if (li.querySelector(".viewcount") == null && match.viewcount != 0) {
      let p = document.createElement("p");
      let div = document.createElement("div");
      div.classList.add("viewcount");
      let img = document.createElement("img");
      img.src = "/static/eye.svg";
      p.textContent = match.viewcount;
      div.appendChild(img);
      div.appendChild(p);
      li.appendChild(div);
    } else {
      if (match.viewcount != 0) {
        li.querySelector(".viewcount p").textContent = match.viewcount;
      } else {
        li.querySelectorAll('.viewcount').forEach(e => e.remove());
      }
    }
  }
}


// Remove streams after animation played and update the streamcount
function removeAfterAnimation(streams, active_streams) {
  if (Array.from(active_streams).length > 0) {
      [...active_streams].forEach(s => {
        s.addEventListener('transitionend', function() {
          this.remove();
          updateStreamCount(streams);
        });
      });
    }
}


// Updates the list of streams on / or /streams via websockets
function updateStreamList(streamlist) {
  // Only do all of this if there is a #streamlist to begin with
  if (document.querySelector("#streamlist")) {
    // Get the location for the streamlist
    let streams = document.querySelector("#streamlist");
    let active_streams = streams.querySelectorAll('.active_stream');

    // Mark inactive streams with the .inactive_stream class (animating it's removal)
    markInaktiveStreams(active_streams, streamlist);

    // Add new streams to the ul #streamlist
    addNewStreams(streams, streamlist);

    // Remove streams after animation played and update the streamcount
    removeAfterAnimation(streams, active_streams);

    // Remove/Add the "no streams" message if the streamcount is zero or > zero
    updateNoStreamsMessage(streams);

    // Update the count of streams displayed
    updateStreamCount(streams);

    // Update the viewcounts next to the numbers
    updateViewcounts(streams, streamlist);
  }

}
