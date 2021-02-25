## How to stream to this site?

To stream to this site you need a streaming source and point it to the right RTMP address. Then you will be able to see the result on this web page, or grab the RTMP stream with a Sink (see below).


### Sources
Which software you use to create an RTMP stream is up to you. Here is a (non-exhaustive) list of different tools

#### [1] Streaming Source: OBS

Open Broadcast Software is a open source video streaming/recording software, that can be used to mix a variety of video and audio sources (webcams, screenshares, ...) and stream the result to every server that understands RTMP streams.

Start OBS, go to `Settings > Stream`  and use something like:

- Service: _Custom..._
- Server: `rtmp://[[[HOSTNAME]]]:1935/live
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

Gstreamer allows many complex setups, but for a very simple test signal use:

```bash
gst-launch-1.0 -e videotestsrc ! queue ! videoconvert ! x264enc ! flvmux streamable=true ! queue ! rtmpsink location='rtmp://[[[HOSTNAME]]]:1935/live/test'
```

#### [4] Streaming Source: ffmpeg

FFMPEG is a command line application that allows you to convert between video and audio files. It can also stream:

```
ffmpeg -re -i input.mp4  -c:v libx264 -preset medium -maxrate 3500k -bufsize 6000k -r 25 -pix_fmt yuv420p -g 60 -c:a aac -b:a 160k -ac 2 -ar 44100 -f flv rtmp://[[[HOSTNAME]]]:1935/live/test
```

### Sinks

If you want to have a more reactive, faster (=lower latency) playback or don't want to display the video on a web page you can also grab the RTMP stream directly without waiting for the 15 second delay of the HLS fragments

#### [1] Sink: VLC player
Start VLC Player and enter `rtmp://[[[HOSTNAME]]]:1935/live/test` as a URL. Replace `test` with the Stream key you made up

#### [2] Sink: ffplay
To minimize the delay (this is the fastest method)  you could also try this if you have `ffmpeg` installed:
```
ffplay -fflags nobuffer rtmp://[[[HOSTNAME]]]:1935/live/test
```

#### [3] Sink: omxplayer
If you want to receive the stream on a Raspi you can use (the usually pre-installed) `omxplayer`:  
```
omxplayer -o hdmi rtmp://[[[HOSTNAME]]].address:1935/live/test;
```