#!/usr/bin/env python 
#-*- coding: utf-8 -*-
import re, os
from pathlib import Path
import datetime as dt
import subprocess
import humanize
from flask import Flask, request, render_template, send_from_directory
from flaskext.markdown import Markdown
from flask_socketio import SocketIO

from .config import initialize_config, APPLICATION_NAME, DEFAULT_CONFIG
from .streams import Stream, StreamList


# Initialization
app = Flask(APPLICATION_NAME, template_folder='../templates', static_folder="../static")
Markdown(app)
app.config["SECRET_KEY"] = "b6e8d852-80fb-473d-9437-7e6a65e84875"
socketio = SocketIO(app)

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
    description = description.replace("[[[PROTECTIONPERIOD]]]", humanize.naturaldelta(dt.timedelta(minutes=config["application"]["password_protection_period"])))

app.logger.info("{} is ready to take requests: {}".format(APPLICATION_NAME, HOSTNAME))

# Create a streamlist
streamlist = StreamList(app.logger).set_max_streams(config["application"]["max_streams"])\
                                   .set_password_protection_period(config["application"]["password_protection_period"])\
                                   .add_from_config(config["stream"])



@app.errorhandler(404)
def page_not_found(e):
    """
    Gets displayed when a page is not found
    Note: Cases where a stream was not found this are handled by streams() below
    """
    return render_template('404.html', application_name=APPLICATION_NAME, page_title=config["application"]["page_title"]), 404


@app.route('/streams/<streamkey>', methods = ['GET'])
def stream(streamkey):
    """
    If there is a stream, display it, otherwise display a missing message
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
        running_since = humanize.naturaldelta(dt.timedelta(seconds=stream.active_since()))
        # Everything ok, return Stream
        return render_template('stream.html', application_name=APPLICATION_NAME, page_title=config["application"]["page_title"], hls_path=config["application"]["hls_path"], streamkey=stream.key, description=stream.description, running_since=running_since)


@app.route('/', methods = ['GET'])
@app.route('/streams', methods = ['GET'])
def streams():
    """
    List the streams and the description.md if set in the config
    """
    # Get a list of active streams and log it
    active_streams = streamlist.listed_streams()
    app.logger.info('Listing active streams: {}'.format(", ".join([str(s) for s in active_streams])))

    # Return the template
    return render_template('streams.html', application_name=APPLICATION_NAME, page_title=config["application"]["page_title"], active_streams=active_streams, description=description, display_description=config["application"]["display_description"], list_streams=config["application"]["list_streams"])


@app.route('/on_publish', methods = ['POST'])
def on_publish():
    """
    Gets called by nginx rtmp module whenver a new incoming stream is created and
    creates a Stream if:
    - there is no existing stream with the same key
    - key and password matches a existing passwort protected (inactive) stream
    - the number of maximum streams specified in the config is not reached yet
    """
    # Request which don't come from localhost are ignored (to avoid malicious stuff)
    if not request.host == "localhost":
        return "Only allowed from localhost", 403

    # Extract some information from the POST data (None if none)
    streamingkey = request.values.get("name")
    password = request.values.get("password")
    description = request.values.get("description")
    unlisted = value_to_flag(request.values.get("unlisted"))
    
    app.logger.debug('\"{}\" came with values \"{}\"'.format(streamingkey, request.values.to_dict(flat=True)))
    app.logger.info('A new RTMP stream connected to the key \"{}\"'.format(streamingkey))
    # Create a stream
    stream = Stream().set_key(streamingkey)\
                     .set_password(password)\
                     .set_description(description)\
                     .set_unlisted(unlisted)

    # Try to add the stream to the streamlist
    if streamlist.add_stream(stream):
        json_list = streamlist.json_list()
        app.logger.debug('Sending JSON list {}'.format(json_list))
        socketio.emit('stream_added', {'key': stream.key, 'list': json_list}, broadcast=True)
        # 201 Created
        return "Created", 201
    else:
        app.logger.info('Stream \"{}\" got denied by Streamlist'.format(streamingkey))
        return "Not Created", 409



@app.route('/on_publish_done', methods = ['POST'])
def on_publish_done():
    """
    Gets called by nginx rtmp module whenever a incoming stream ends
    If the stream was password protected the stream gets just deactivated till
    someone logs on again
    """
    # Request which don't come from localhost are ignored (to avoid malicious stuff)
    if not request.host == "localhost":
        return "Only allowed from localhost", 403
    streamingkey = request.values.get("name")
    app.logger.info('Existing RTMP stream \"{}\" ended'.format(streamingkey))
    streamlist.remove_stream(streamingkey)
    json_list = streamlist.json_list()
    app.logger.debug('Sending JSON list {}'.format(json_list))
    socketio.emit('stream_removed', {'key': streamingkey, 'list': json_list}, broadcast=True)

    return "Ok", 200



@socketio.on('client_connected')
def client_connected(data):
    app.logger.info('Client connected via socket.io')
    json_list = streamlist.json_list()
    app.logger.debug('Sending JSON list {}'.format(json_list))
    socketio.emit('stream_list', {'list': json_list})



def value_to_flag(value) -> bool:
    """
    Return False if the value was None, otherwise return wether it was in the list
    of true values
    """
    if value is None:
        return False

    return value.lower() in ["1", "yes", "true", '']
    

if __name__ == '__main__':
    socketio.run(app)