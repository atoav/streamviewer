#!/usr/bin/env python 
#-*- coding: utf-8 -*-
import re, os
from pathlib import Path
import datetime as dt
import subprocess
from flask import Flask, request, render_template, send_from_directory
from flaskext.markdown import Markdown

from .config import initialize_config, APPLICATION_NAME, DEFAULT_CONFIG


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
    description = description.replace("[[[RTMP-APP-NAME]]]/", config["application"]["rtmp-app-name"])

app.logger.info("{} is ready to take requests: {}".format(APPLICATION_NAME, HOSTNAME))






@app.route('/streams/<streamkey>', methods = ['GET'])
def stream(streamkey):
    """
    If there is a stream, display it, otherwise note that the stream is missing
    """
    app.logger.info('200, Access to /{}'.format(streamkey))
    app.logger.debug("Looking for {}/{}.m3u8".format(config["application"]["hls_path"],  streamkey))

    # Strip potential trailing slashes
    streamkey = streamkey.rstrip("/")

    # Get a list of the active streams
    active_streams = list_streams()
    active_streams = [str(s).rsplit("/")[-1].replace(".m3u8", "") for s in active_streams]

    # Render a different Template if the stream is missing
    if streamkey not in active_streams:
        # Stream was Missing, log warning
        app.logger.warning("Looking for stream {}, but it didn't exist".format(streamkey))
        return render_template("stream_missing.html", application_name=APPLICATION_NAME, page_title=config["application"]["page_title"], streamkey=streamkey, list_streams=config["application"]["list_streams"], 404)
    else:
        # Everything ok, return Stream
        return render_template('stream.html', application_name=APPLICATION_NAME, page_title=config["application"]["page_title"], hls_path=config["application"]["hls_path"], streamkey=streamkey)



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
    # Get a lsit of active streams and log it
    active_streams = list_streams()
    active_streams = [str(s).rsplit("/")[-1].replace(".m3u8", "") for s in active_streams]
    app.logger.info('Listing active streams: {}'.format(", ".join([str(s) for s in active_streams])))

    # Return the template
    return render_template('streams.html', application_name=APPLICATION_NAME, page_title=config["application"]["page_title"], active_streams=active_streams, description=description, display_description=config["application"]["display_description"], list_streams=config["application"]["list_streams"])



def list_streams():
    """
    Return a list of currently active streams, unless deactivated in config.toml
    """
    if config["application"]["list_streams"]:
        hls_path = Path(config["application"]["hls_path"].rstrip("/"))
        return list(hls_path.glob('*.m3u8'))
    else:
        return []


