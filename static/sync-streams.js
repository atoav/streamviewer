var socket = io();

socket.on('connect', function() {
    socket.emit();
});

socket.on('stream_list', function(data) {
    console.log('Received stream list');
    var streamlist = JSON.parse(data["list"])
    updateStreamList(streamlist);
});

socket.on('stream_added', function(data) {
    console.log('Stream ' + data['key'] + ' added.');
    var streamlist = JSON.parse(data["list"])
    updateStreamList(streamlist);
});

socket.on('stream_removed', function(data) {
    console.log('Stream ' + data['key'] + ' removed.');
    var streamlist = JSON.parse(data["list"])
    updateStreamList(streamlist);
});



function extractStreamKey(e) {
  for (const c of e.classList){
    if (c.startsWith('stream-')) {
      return c.substring(7);
    }
  }
}

function hasStream(streamlist, k) {
  return streamlist.some(({ key }) => key === k);
}


/* Remove all active streams */
function updateStreamList(streamlist) {

  // Get the location for the streamlist
  let streams = document.querySelector("#streamlist");
  let active_streams = streams.querySelectorAll('.active_stream');

  // Remove all streams that are not active anymore
  active_streams.forEach(e => {
    let key = extractStreamKey(e);
    if (!hasStream(streamlist, key)) { 
      e.classList.add('inactive_stream');
    }
  });

  // Remove streams after animation played
  active_streams[0].addEventListener('transitionend', function() {
    [...active_streams].forEach((s) => s.parentNode.removeChild(s))
  });


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

  // Add or remove the notification "There are currently no active streams" based on the streamcount
  let existingStreams = Array.from(streams.querySelectorAll('.active_stream')).map(e => extractStreamKey(e))
  if (existingStreams.length > 0) {
    // If there are streams remove the "no streams"-message
    if (document.getElementById("no-stream-notice") !== null) { 
      document.getElementById("no-stream-notice").remove();
    }
  }else{
    // If there are no streams add a message
    let h2 = document.createElement("h2");
    h2.textContent = "There are currently no active streams"
    h2.id = "no-stream-notice";
    streams.appendChild(h2);
  }

  // Update the streamcount in the title
  if (document.getElementById("streamheader") !== null) { 
    document.getElementById("streamheader").textContent = "Active Streams [" + existingStreams.length + "]";
  }

}
