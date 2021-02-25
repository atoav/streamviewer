#!/usr/bin/env python 
#-*- coding: utf-8 -*-
import re
from pathlib import Path
import datetime as dt
import sqlite3
from flask import Flask, request, render_template, send_from_directory

from .config import initialize_config, APPLICATION_NAME, DEFAULT_CONFIG


# Initialization
app = Flask(APPLICATION_NAME, template_folder='../templates', static_folder="../static")

# Initialize the configuration (create a default one if needed)
config = initialize_config(app.logger)

app.logger.info('Ready to take requests')





# This gets run for each request
@app.route('/stream/<streamkey>', methods = ['GET'])
def streamview(streamkey):
    app.logger.info('200, Access to /{}'.format(streamkey))
    hls_path = config["application"]["hls_path"].rstrip("/")
    app.logger.info("Looking for {}/{}.m3u8".format(hls_path,  streamkey))
    streamkey = streamkey.rstrip("/")
    active_streams = list_streams()
    active_streams = [str(s).rsplit("/")[-1].replace(".m3u8", "") for s in active_streams]
    if streamkey not in active_streams:
        return render_template("streammissing.html", application_name=APPLICATION_NAME, page_title=config["application"]["page_title"], streamkey=streamkey)
    else:
        return render_template('stream.html', application_name=APPLICATION_NAME, page_title=config["application"]["page_title"], hls_path=hls_path, streamkey=streamkey)

@app.route('/', methods = ['GET'])
@app.route('/stream', methods = ['GET'])
def streamlist():
    app.logger.info('Listing streams')
    active_streams = list_streams()
    active_streams = [str(s).rsplit("/")[-1].replace(".m3u8", "") for s in active_streams]
    hls_path = config["application"]["hls_path"].rstrip("/")
    app.logger.info('Active streams: {}'.format(", ".join([str(s) for s in active_streams])))
    return render_template('streamlist.html', application_name=APPLICATION_NAME, page_title=config["application"]["page_title"], active_streams=active_streams)



def list_streams():
    """
    Return a list of currently active streams
    """
    hls_path = Path(config["application"]["hls_path"].rstrip("/"))
    return list(hls_path.glob('*.m3u8'))


