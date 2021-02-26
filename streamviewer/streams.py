#!/usr/bin/env python 
#-*- coding: utf-8 -*-
from typing import Optional, NewType, List
import datetime as dt

Seconds = NewType('Seconds', int)


def str_if_not_None(value, this, that="") -> str:
    if value is not None:
        return str(this)
    else:
        return str(that)

def str_if_true(value, this, that="") -> str:
    if value:
        return str(this)
    else:
        return str(that)



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
        self.unlisted = True

    def __repr__(self):
        """
        Stream is represented by its key
        """
        return self.key

    def __cmp__(self, other):
        return self.key == other.key

    def __str__(self) -> str:
        inactive = str_if_true(self.active, "inactive")
        unlisted = str_if_true(not self.unlisted, "unlisted")
        description = str_if_not_None(self.description, "with description")
        password = str_if_not_None(self.password, "password-protected")

        attributes = [a for a in [unlisted, inactive, password, description] if a != ""]

        if len(attributes) > 0:
            return "{} ({})".format(self.key, ", ".join(attributes))
        return "{}".format(self.key)

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
                    existing_stream = stream
                    self.logger.info("Replaced existing stream {} because a valid password was supplied".format(stream))
                    return True
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

        # Check the number of active streams first
        if len([s for s in self.streams if s.active]) >= self.max_streams:
            self.logger.info("Not adding new stream \"{}\" because the maximum of {} active streams is reached".format(stream, self.max_streams))
            return False

        # If the stream already exist check the password (if there is one) and
        # whether that password is still protective or not
        if self.has_stream(stream):
            self.logger.debug("The new stream \"{}\" already exists in list".format(stream))
            return self.replace_matching_stream(stream)

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


