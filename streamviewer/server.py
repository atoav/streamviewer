#!/usr/bin/env python 
#-*- coding: utf-8 -*-
import re
import datetime as dt
import sqlite3
from flask import Flask, request, render_template

from .config import initialize_config, APPLICATION_NAME, DEFAULT_CONFIG


# Initialization
app = Flask(APPLICATION_NAME, template_folder='../templates', static_folder="../static")

# Initialize the configuration (create a default one if needed)
config = initialize_config(app.logger)

app.logger.info('Ready to take requests')




# This gets run for each request
@app.route('/', methods = ['GET'])
def get():
    """
    This function runs when a GET request on / is received.
    """
    return render_template('default.html', application_name=APPLICATION_NAME, page_title=config["application"]["page_title"])


# This gets run for each request
@app.route('/<streamkey>', methods = ['GET'])
def stream(streamkey):
    app.logger.info('200, Access to /{}'.format(streamkey))
    hls_path = config["application"]["hls_path"].rstrip("/")
    streamkey = streamkey.rstrip("/")
    return render_template('stream.html', application_name=APPLICATION_NAME, page_title=config["application"]["page_title"], hls_path=hls_path, streamkey=streamkey)

