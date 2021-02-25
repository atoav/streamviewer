#!/usr/bin/env python 
#-*- coding: utf-8 -*-
import re, os
from pathlib import Path
import datetime as dt
import sqlite3
from flask import Flask, request, render_template, send_from_directory
from flaskext.markdown import Markdown

from .config import initialize_config, APPLICATION_NAME, DEFAULT_CONFIG


# Initialization
app = Flask(APPLICATION_NAME, template_folder='../templates', static_folder="../static")
Markdown(app)

# Initialize the configuration (create a default one if needed)
config = initialize_config(app.logger)
config["application"]["hls_path"] = config["application"]["hls_path"].rstrip("/")

with open(os.path.join(app.instance_path, "../static/description.md")) as f:
    description = f.read()

app.logger.info("{} is ready to take requests: {}".format(APPLICATION_NAME, flask.request.host_url))






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
        app.logger.warning("Looking for stream {}, but it didn't exist".format(streamkey))
        return render_template("stream_missing.html", application_name=APPLICATION_NAME, page_title=config["application"]["page_title"], streamkey=streamkey)
    else:
        return render_template('stream.html', application_name=APPLICATION_NAME, page_title=config["application"]["page_title"], hls_path=config["application"]["hls_path"], streamkey=streamkey)


@app.route('/', methods = ['GET'])
@app.route('/streams', methods = ['GET'])
def streams():
    """
    List the streams
    """
    active_streams = list_streams()
    active_streams = [str(s).rsplit("/")[-1].replace(".m3u8", "") for s in active_streams]
    app.logger.info('Listing active streams: {}'.format(", ".join([str(s) for s in active_streams])))
    return render_template('streams.html', application_name=APPLICATION_NAME, page_title=config["application"]["page_title"], active_streams=active_streams, description=description, display_description=config["application"]["display_description"], list_streams=config["application"]["list_streams"])



def list_streams():
    """
    Return a list of currently active streams
    """
    if config["application"]["list_streams"]:
        hls_path = Path(config["application"]["hls_path"].rstrip("/"))
        return list(hls_path.glob('*.m3u8'))
    else:
        return []


