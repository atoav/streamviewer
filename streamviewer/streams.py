#!/usr/bin/env python 
#-*- coding: utf-8 -*-
import json
from typing import Optional, NewType, List, Any
import datetime as dt

Seconds = NewType('Seconds', int)


def str_if_not_None(value, this, that="") -> str:
    """
    Return this if the supplied value is not None
    otherwise return that (per default a empty string)
    """
    if value is not None:
        return str(this)
    else:
        return str(that)

def str_if_true(value, this, that="") -> str:
    """
    Return this if the supplied value was True
    otherwise return that (per default a empty string)
    """
    if value:
        return str(this)
    else:
        return str(that)


def none_if_no_key_value_otherwise(d: dict, key: str, that=None) -> Optional[Any]:
    """
    Return the value of dict[key] if the key exists
    otherwise return that (per default None)
    """
    if not key in d.keys():
        return that
    return d[key]


def value_to_flag(value) -> bool:
    """
    Return False if the value was None, otherwise return wether it was in the list
    of true values
    """
    if value is None:
        return False

    return value.lower() in ["1", "yes", "true", '']


class Stream():
    """
    A Stream is _the representation_ of a stream. Streams are actually handled by
    the Nginx RTMP module and get registered by a POST request from nginx to
    /on_publish and de-registered in a similar fashion by a POST request to
    /on_publish_done.

    This uses a builder pattern, so you can do things like:
    stream = Stream().set_key("Foo")\
                     .set_password("1234")\
                     .set_description("# Super cool stream *stream*")
    """
    def __init__(self):
        self.creation_time = dt.datetime.now()
        self.deactivation_time = None
        self.active = True
        self.key = None
        self.password = None
        self.description = None
        self.unlisted = None
        self.protected = None

    def __repr__(self):
        """
        Stream is represented by its key
        """
        return self.key

    def __cmp__(self, other):
        return self.key == other.key

    def __str__(self) -> str:
        inactive = str_if_true(self.active, "inactive")
        unlisted = str_if_true(self.unlisted, "unlisted")
        protected = str_if_true(self.protected, "protected")
        description = str_if_not_None(self.description, "with description")
        password = str_if_not_None(self.password, "password-protected")

        attributes = [a for a in [protected, unlisted, inactive, password, description] if a != ""]

        if len(attributes) > 0:
            return "{} ({})".format(self.key, ", ".join(attributes))
        return "{}".format(self.key)

    def to_json(self):
        return json.dumps(self, default=jsonconverter, 
            sort_keys=True, indent=4)

    def set_key(self, key) -> 'Stream':
        """
        Set a streams key (must be set)
        """
        self.key = key
        return self

    def set_password(self, password) -> 'Stream':
        """
        Set the streams password (must not be set)
        """
        self.password = password
        return self

    def set_description(self, description) -> 'Stream':
        """
        Set the streams description (must not be set)
        This will get rendered as markdown
        """
        self.description = description
        return self

    def set_unlisted(self, unlisted: bool=True) -> 'Stream':
        """
        Set the stream to listed or unlisted (must not be set)
        """
        self.unlisted = unlisted
        return self

    def set_protected(self, protected: bool=True) -> 'Stream':
        """
        Set the stream to listed or protected (must not be set)
        """
        self.protected = protected
        return self
    
    def is_valid_password(self, password) -> bool:
        """
        Returns true if the provided password matches this streams password
        """
        if self.password is None:
            return True
        return password == self.password

    def has_password_protection(self, password_protection_period) -> bool:
        """
        Return True if the Stream has password protection
        If the stream is active also return True
        """
        delta = self.inactive_since()
        if delta is None:
            return True
        return delta < password_protection_period

    def deactivate(self) -> 'Stream':
        """
        Set the stream to inactive (used to keep an inactive password protected 
        stream in the list)
        """
        self.active = False
        self.deactivation_time = dt.datetime.now()
        return self

    def activate(self) -> 'Stream':
        """
        Activate a stream (default on creation), resets the deactivation time
        """
        self.active = True
        self.deactivation_time = False

    def inactive_since(self) -> Optional['Seconds']:
        """
        Returns None if the Stream is active, otherwise return the seconds since
        deactivation
        """
        if self.active:
            return None
        delta = dt.datetime.now() - self.deactivation_time
        return delta.total_seconds()

    def active_since(self) -> Optional['Seconds']:
        """
        Returns None if the Stream is inactive, otherwise return the seconds since
        creation
        """
        if not self.active:
            return None
        delta = dt.datetime.now() - self.creation_time
        return delta.total_seconds()


class StreamList():
    """
    The StreamList handles all List related duties.
    """
    def __init__(self, logger):
        self.logger = logger
        self.streams = []
        self.max_streams = None
        self.password_protection_period = 0
        self.free_choice = False
        self.logger.debug("Created StreamList")

    def __iter__(self):
        """
        Allows iteration over the 
        """
        for stream in self.streams:
            yield stream

    def set_max_streams(self, n) -> 'StreamList':
        """
        Sets the maximum number of streams allowed.
        Streams that get added after this will not be accepted
        """
        if n >= 0:
            self.max_streams = int(n)
            self.logger.debug("Set max_streams to {}".format(self.max_streams))
        return self

    def set_free_choice(self, free: bool=False) -> 'StreamList':
        """
        Sets the maximum number of streams allowed.
        Streams that get added after this will not be accepted
        """
        self.free_choice = free
        if self.free_choice:
            self.logger.warning("Set free_choice to {} (this means everybody on the same net can stram to this service!)".format(self.free_choice))
        else:
            self.logger.warning("Set free_choice to {} (this means only streams listed in the config can be used)".format(self.free_choice))
        return self

    def set_password_protection_period(self, minutes: int) -> 'StreamList':
        """
        Sets the password protection period in minutes. This is the duration for
        which the stream will be reserved after deactivation of the Stream.
        This protection is non-persistence and will vanish after a restart
        """
        if minutes>= 0:
            self.password_protection_period = minutes*60
            self.logger.debug("Set password_protection_period to {} seconds".format(self.password_protection_period))
        else:
            self.logger.warning("Warning: the password_protection_period had a negative value and was ignored {}".format(minutes))
        return self

    def active_streams(self) -> List['Stream']:
        """
        Return a list of active streams
        """
        return [s for s in self.streams if s.active]

    def listed_streams(self) -> List['Stream']:
        """
        Return a list of streams that should be listed (active and not unlisted)
        """
        return [s for s in self.active_streams() if not s.unlisted]

    def protected_streams(self) -> List['Stream']:
        """
        Return a list of protected streams
        """
        return [s for s in self.streams if s.protected]

    def inactive_protected_streams(self) -> List['Stream']:
        """
        Return a list of inactive protected streams
        """
        return [s for s in self.streams if s.protected and not s.active]

    def json_list(self) -> str:
        return json.dumps(self.listed_streams(), default=jsonconverter, 
            sort_keys=True, indent=4)

    def has_stream(self, stream) -> bool:
        """
        Return True if a stream of that name exists
        """
        return any([s.key == stream.key for s in self.streams])

    def has_active_stream(self, stream) -> bool:
        """
        Return True if a active stream of that name exists
        """
        return any([s.key == stream.key for s in self.streams if s.active])

    def has_inactive_stream(self, stream) -> bool:
        """
        Return True if a inactive stream of that name exists
        """
        return any([s.key == stream.key for s in self.streams if not s.active])

    def has_inactive_protected_stream(self, stream) -> bool:
        """
        Return True if a inactive protected stream of that name exists
        """
        return any([s.key == stream.key for s in self.streams if not s.active and s.protected])

    def get_stream(self, key) -> Optional['Stream']:
        """
        Returns None if no matching stream was found, 
        otherwise the first matching stream is returned
        """
        matches = [s for s in self.streams if s.key == key]
        if len(matches) == 0:
            return None
        return matches[0]

    def replace_matching_stream(self, stream: 'Stream') -> bool:
        """
        Replace the first matching stream if the password is valid or the
        password protection period has perished
        """
        for existing_stream in self.streams:
            if existing_stream.key == stream.key:
                if existing_stream.is_valid_password(stream.password):
                    if existing_stream.protected:
                        stream.set_protected(True)
                    p = str_if_true(existing_stream.protected, "(protected) ")
                    existing_stream = stream
                    self.logger.info("Replaced existing {}stream {} because a valid password was supplied".format(p, stream))
                    return True
                elif existing_stream.protected:
                    if existing_stream.password is None:
                        self.logger.info("Replaced existing (protected) stream {}, because the protected stream has no password set".format(stream))
                        return True
                    else:
                        self.logger.info("Didn't accept new stream {}, because a existing stream is protected".format(stream))
                        return False
                elif not existing_stream.has_password_protection(self.password_protection_period):
                    self.logger.info("Replaced existing stream {} because its password protection period is over ({}/{})".format(existing_stream, existing_stream.inactive_since(), self.password_protection_period))
                    existing_stream = stream
                    return True
        self.logger.info("Didn't accept new stream {}, because a existing stream is protected".format(stream))
        return False

    def deactivate_matching_stream(self, stream: 'Stream') -> 'StreamList':
        """
        Deactivate the first matching stream
        """
        for existing_stream in self.streams:
            if existing_stream == stream:
                existing_stream = stream.deactivate()
                self.logger.info("Deactivated existing stream {}".format(stream))
                return self

    def add_stream(self, stream: 'Stream') -> bool:
        """
        Add a new Stream. If the key is protected by a password check for the password
        or if the password protection period is over. Check also if the number of max 
        streams is not exceeded.

        Returns True if the stream was added, False otherwise
        """

        # Check the number of active streams first (reserving space for the protected streams)
        if len([s for s in self.streams if s.active]) - len(self.inactive_protected_streams()) >= self.max_streams:
            self.logger.info("Not adding new stream \"{}\" because the maximum number of {} active streams is reached".format(stream, self.max_streams))
            return False

        # Initially add protected streams from config. Streams supplied by flask are
        # always active initially so cannot be set this way
        if stream.protected and not stream.active:
            self.streams.append(stream)
            self.logger.info("Added new protected stream \"{}\" from config to list".format(stream))
            return True

        # If the stream already exist check the password (if there is one) and
        # whether that password is still protective or not
        if self.has_stream(stream):
            self.logger.debug("The new stream \"{}\" already exists in list".format(stream))
            return self.replace_matching_stream(stream)

        # If the stream wasn't replaced above, and free choice doesn't exist, deny
        if not self.free_choice:
            self.logger.warning("Didn't add stream \"{}\" because it was not listed in the config (free choice of stream keys is disabled)".format(stream))
            return False

        # If none of the above applies append the Stream to the list
        self.streams.append(stream)
        self.logger.info("Added new stream \"{}\" to list".format(stream))

        return True

    def remove_stream(self, key: str) -> 'StreamList':
        """
        Remove or deactivates the stream with the fiven key if it exists
        The stream is removed if it has no password, or the password protection
        period is over. Otherwise it is just deactivated
        """
        existing_stream = self.get_stream(key)

        # Should there be no existing stream with that key, return
        if existing_stream is None:
            self.logger.debug("Tried to remove existing stream {}, but it was None? This should not happen.".format(key))
            return self

        # If the existing stream is protected, deactivate it instead of removing it
        if existing_stream.protected:
            return self.deactivate_matching_stream(existing_stream)

        # Should there be no password protection or the period is over, remove the stream
        if existing_stream.password is None:
            self.streams = [s for s in self.streams if s.key != key]
            self.logger.info("Removed existing stream {} because it was not password protected".format(existing_stream))
            return self

        if not existing_stream.has_password_protection(self.password_protection_period):
            self.streams = [s for s in self.streams if s.key != key]
            self.logger.info("Removed existing stream {} because its password protection period is over ({}/{})".format(existing_stream, existing_stream.inactive_since(), self.password_protection_period))
            return self

        # otherwise deactivate it
        return self.deactivate_matching_stream(existing_stream)


    def add_streams_from_config(self, config) -> 'Streamlist':
        """
        Adds all streams from the config as protected/deactivated streams
        This is a mechanism to permanently "reserve" certain stream keys
        """
        for stream in config["stream"]["key"]:
            assert(type(stream), dict)
            self.logger.debug("Stream of type \"{}\" was {}".format(type(stream), stream))
            # Parse the values from the configs
            name        = none_if_no_key_value_otherwise(stream, key="name")
            password    = none_if_no_key_value_otherwise(stream, key="password")
            description = none_if_no_key_value_otherwise(stream, key="description")
            unlisted    = none_if_no_key_value_otherwise(stream, key="name")
            unlisted = value_to_flag(unlisted)

            # The only field that needs to be present is "name"
            if name is None:
                self.logger.warning("Found a stream in the configuration with no \"name\" defined!")
                continue

            # Construct a protected but deactivated stream with all other values
            # coming from the config
            protected_stream = Stream().set_key(name)\
                                       .set_password(password)\
                                       .set_description(description)\
                                       .set_unlisted(unlisted)\
                                       .set_protected(True)\
                                       .deactivate()

            # Add the new protected stream to the streamlist
            self.add_stream(protected_stream)

        return self




def jsonconverter(o):
    if isinstance(o, dt.datetime):
        return o.__str__()
    else:
        return o.__dict__