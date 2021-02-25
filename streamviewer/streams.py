#!/usr/bin/env python 
#-*- coding: utf-8 -*-
from typing import Optional

class Stream():
    def __init__(self):
        key = None
        password = None
        description = None

    def __repr__(self):
        return self.key


    def set_key(self, key) -> 'Stream':
        self.key = key
        return self

    def set_password(self, password) -> 'Stream':
        self.password = password
        return self

    def set_description(self, description) -> 'Stream':
        self.description = description
        return self
    
    def is_valid_password(self, password) -> bool:
        if self.password is None:
            return True
        return password == self.password


class StreamList():
    def __init__(self):
        self.streams = []
        self.max_streams = None

    def __iter__(self):
        for stream in self.streams:
            yield stream

    def set_max_streams(self, n) -> 'StreamList':
        if n >= 0:
            self.max_streams = n
        return self

    def has_stream(self, stream) -> bool:
        return any([s.key == stream for s in self.streams])

    def get_stream(self, stream) -> Optional['Stream']:
        matches = [s for s in self.streams if s.key == stream]
        if len(matches) == 0:
            return None
        return matches[0]

    def replace_matching_stream(self, stream: 'Stream') -> bool:
        for existing_stream in self.streams:
            if existing_stream == stream:
                if existing_stream.is_valid_password(stream.password):
                    existing_stream = stream
                    return True
        return False

    def add_stream(self, stream: 'Stream') -> bool:
        if len(self.streams) >= self.max_streams:
            return False

        # If the stream already exist check the password (if there is one) and update it
        if self.has_stream(stream):
            return replace_matching_stream(stream)

        self.streams.append(stream)

        return True

    def remove_stream(self, key: str) -> 'StreamList':
        self.streams = [s for s in self.streams if s != key]
        return self