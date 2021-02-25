#!/usr/bin/env python 
#-*- coding: utf-8 -*-
import re, os
from pathlib import Path
import datetime as dt
import subprocess
from flask import Flask, request, render_template, send_from_directory
from flaskext.markdown import Markdown

from .config import initialize_config, APPLICATION_NAME, DEFAULT_CONFIG
from .streams import Stream, StreamList


# Initialization
app = Flask(APPLICATION_NAME, template_folder='../templates', static_folder="../static")
Markdown(app)

# Get some strings
SCRIPTDIR = os.path.dirname(os.path.realpath(__file__))
HOSTNAME  = subprocess.check_output('hostname').decode('utf8')

# Initialize the configuration (create a default one if needed)
config = initialize_config(app.logger)
config["application"]["hls_path"] = config["application"]["hls_path"].rstrip("/")


# Read the description.md from the static folder
with open(os.path.join(SCRIPTDIR, "../static/description.md")) as f:
    description = f.read()
    # Replace the placeholder values
    description = description.replace("[[[HOSTNAME]]]", config["application"]["hostname"])
    description = description.replace("[[[RTMP-PORT]]]", config["application"]["rtmp-port"])
    description = description.replace("[[[RTMP-APP-NAME]]]", config["application"]["rtmp-app-name"])

app.logger.info("{} is ready to take requests: {}".format(APPLICATION_NAME, HOSTNAME))

# Create a streamlist
streamlist = StreamList().set_max_streams(config["application"]["max_streams"])



@app.route('/streams/<streamkey>', methods = ['GET'])
def stream(streamkey):
    """
    If there is a stream, display it, otherwise note that the stream is missing
    """
    app.logger.info('200, Access to /{}'.format(streamkey))

    # Strip potential trailing slashes
    streamkey = streamkey.rstrip("/")
    stream = streamlist.get_stream(streamkey)

    # Render a different Template if the stream is missing
    if stream is None:
        # Stream was Missing, log warning
        app.logger.warning("Looking for stream {}, but it didn't exist".format(streamkey))
        return render_template("stream_missing.html", application_name=APPLICATION_NAME, page_title=config["application"]["page_title"], streamkey=streamkey, list_streams=config["application"]["list_streams"]), 404
    else:
        app.logger.debug("Looking for {}/{}.m3u8".format(config["application"]["hls_path"],  streamkey))
        # Everything ok, return Stream
        return render_template('stream.html', application_name=APPLICATION_NAME, page_title=config["application"]["page_title"], hls_path=config["application"]["hls_path"], streamkey=stream.key, description=stream.description)



@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html', application_name=APPLICATION_NAME, page_title=config["application"]["page_title"]), 404



@app.route('/', methods = ['GET'])
@app.route('/streams', methods = ['GET'])
def streams():
    """
    List the streams
    """
    # Get a list of active streams and log it
    active_streams = [s.key for s in streamlist]
    app.logger.info('Listing active streams: {}'.format(", ".join([str(s) for s in active_streams])))

    # Return the template
    return render_template('streams.html', application_name=APPLICATION_NAME, page_title=config["application"]["page_title"], active_streams=active_streams, description=description, display_description=config["application"]["display_description"], list_streams=config["application"]["list_streams"])


@app.route('/on_publish', methods = ['POST'])
def on_publish():
    """
    Gets called by nginx rtmp module whenver a new stream is created
    """
    if not request.host == "localhost":
        return "Only allowed from localhost", 403
    streamingkey = request.values.get("name")
    password = request.values.get("password")
    description = request.values.get("description")
    app.logger.info('A new RTMP stream called \"{}\" connected'.format(streamingkey))

    stream = Stream().set_key(streamingkey)\
                     .set_password(password)\
                     .set_description(description)
    if streamlist.add_stream(stream):
        app.logger.info('Stream \"{}\" got added to Streamlist'.format(streamingkey))
        # 201 Created
        return "Created", 201
    else:
        app.logger.info('Stream \"{}\" got denied by Streamlist'.format(streamingkey))
        return "Not Created", 409



@app.route('/on_publish_done', methods = ['POST'])
def on_publish_done():
    """
    Gets called by nginx rtmp module whenever a stream is ended
    """
    if not request.host == "localhost":
        return "Only allowed from localhost", 403
    streamingkey = request.values.get("name")
    app.logger.info('Existing RTMP stream \"{}\" ended'.format(streamingkey))
    streamlist.remove_stream(streamingkey)

    return "Ok", 200





def stream_exists(streamkey) -> bool:
    """
    Return true when the stream 
    """
    active_streams = list_streams()
    active_streams = [str(s).rsplit("/")[-1].replace(".m3u8", "") for s in active_streams]
    return streamkey in active_streams


def list_streams():
    """
    Return a list of currently active streams, unless deactivated in config.toml
    """
    if config["application"]["list_streams"]:
        hls_path = Path(config["application"]["hls_path"].rstrip("/"))
        return list(hls_path.glob('*.m3u8'))
    else:
        return []
