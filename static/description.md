## How to stream to this site?

To stream to this site you need a streaming [source](#Sources) and point it to the right RTMP address. Then you will be able to see the stream on this web page, or grab the RTMP stream directly with a [software sink](#Sinks).

### What is an RTMP Address?
To send a stream you have to use the correct RTMP Address (every server has a different one.  

A RTMP Address consists of the following pieces (in that order):  

- **Protocol:** `rtmp://`
- **Hostname:** `[[[HOSTNAME]]]`  
- **Port:** `:[[[RTMP-PORT]]]`
- **RTMP-Application Name:** `/[[[RTMP-APP-NAME]]]`
- **Stream Key** (of your choice): e.g. `/test`
- **Other Options** (optional, started with `?` combined with `&`):
    - **Description:** `?description=blabla`
    - **Password:** `&password=1234`
    - **Unlisted:** `&unlisted`

If we combine all of the above in that order we would get:  
```
rtmp://[[[HOSTNAME]]]:[[[RTMP-PORT]]]/[[[RTMP-APP-NAME]]]/test?description=blabla&password=1234&unlisted
```

That looks like a lot, but for the start you can skip everything after (and including) the `?` — if you are just trying the software out it makes a lot of sense to reduce the things that can go wrong in the beginning.

### What are the Options?

Passwords protect the used stream key (in the example above `test`) for [[[PROTECTIONPERIOD]]] after the stream has become inactive. This protection is not guaranteed because it won't persist after the server restarted.

Descriptions allow you to display text underneath the streams site. The descriptions support [Markdown](https://www.markdownguide.org/basic-syntax/) for styling. Just make sure to convert the text with a [urlencode tool](https://www.urlencoder.org/) first, otherwise it won't work.

Unlisted is for when your stream should not be listed in the list at the main site (so only people with knowledge of the URL can see it).


### Sources
To create a stream you need a source that sends video data in realtime. Every software that can produce a RTMP stream in the right shape and size will work. Which software (or hardware) you use is up to you. Here is a (non-exhaustive) list of different tools that might work:

#### [1] Streaming Source: OBS

[Open Broadcast Software](https://obsproject.com/) is a open source video streaming/recording software, that can be used to mix a variety of video and audio sources (webcams, screenshares, ...) and stream the result to every server that understands RTMP streams.

Start OBS, go to `Settings > Stream`  and use something like:

- Service: _Custom..._
- Server: `rtmp://[[[HOSTNAME]]]:[[[RTMP-PORT]]]/[[[RTMP-APP-NAME]]]`
- Stream Key: Arbitrary, e.g. `test`

The setup the video format in `Settings > Output`:

- Switch to `Advanced`
- Select `H264` or `x264` ad an encoder (Hardware prefered over Software)
- Bitrate between `2000` and `8000`
- Keyframe Interval: `2`
- Profile: `main` or `baseline`
- Max B-frames: `0`

Now save the settings and click on _Start Streaming_ .  If nothing complains it should already work and you should be able to view your stream at `[[[HOSTNAME]]]/streams/test` (replace `test` with your own stream key of course)

#### [2] Streaming Source: Atem Mini
By using tricks you can also add the RTMP address to the Blackmagic Atem Mini and stream directly to it

#### [3] Streaming Source: Gstreamer

[Gstreamer](https://gstreamer.freedesktop.org/) allows many complex setups, but for a very simple test signal use:

```bash
gst-launch-1.0 -e videotestsrc ! queue ! videoconvert ! x264enc ! flvmux streamable=true ! queue ! rtmpsink location='rtmp://[[[HOSTNAME]]]:[[[RTMP-PORT]]]/[[[RTMP-APP-NAME]]]/test'
```

#### [4] Streaming Source: ffmpeg

[ffmpeg](https://ffmpeg.org/) is a command line application that allows you to convert between video and audio files. It can also stream:

```
ffmpeg -re -i input.mp4  -c:v libx264 -preset medium -maxrate 3500k -bufsize 6000k -r 25 -pix_fmt yuv420p -g 60 -c:a aac -b:a 160k -ac 2 -ar 44100 -f flv rtmp://[[[HOSTNAME]]]:[[[RTMP-PORT]]]/[[[RTMP-APP-NAME]]]/test
```

This might look a little bit intimidating, but you only need to swap out `input.mp4` for your video file and you are good to go.

### Sinks

If you want to have a more reactive, faster (=lower latency) playback or don't want to display the video on a web page you can also grab the RTMP stream directly without waiting for the 15 second delay of the HLS fragments.

#### [1] Sink: VLC player
Start [VLC Player](https://www.videolan.org/vlc/index.html), go to `Media > Open Network Stream` and enter `rtmp://[[[HOSTNAME]]]:[[[RTMP-PORT]]]/[[[RTMP-APP-NAME]]]/test` as a URL. Replace `test` with the Stream key you made up

#### [2] Sink: ffplay
If you have [ffmpeg](https://ffmpeg.org/) installed you also have ffplay installed. It can be keep the playback delay to a minimum (this is the fastest method) and playing back the stream is quite simple:
```
ffplay -fflags nobuffer rtmp://[[[HOSTNAME]]]:[[[RTMP-PORT]]]/[[[RTMP-APP-NAME]]]/test
```

#### [3] Sink: omxplayer
[omxplayer](https://www.raspberrypi.org/documentation/raspbian/applications/omxplayer.md) is preinstalled on every Raspberry Pi (if you use Raspbian). To output a stream to the HDMI Output of a Raspi use:
```
omxplayer -o hdmi rtmp://[[[HOSTNAME]]].address:[[[RTMP-PORT]]]/[[[RTMP-APP-NAME]]]/test;
```