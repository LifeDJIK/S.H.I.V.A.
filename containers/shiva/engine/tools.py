#!/usr/bin/python
# coding=utf-8
# pylint: disable=I0011,C0103,E1101,R0201,R0903
"""
S.H.I.V.A. - Social network History & Information Vault & Analyser

Tools
"""


import datetime
import cherrypy
import logging
import pickle
import base64
import time

from cherrypy.lib.sessions import Session


def secureheaders():
    """ Secure headers """
    headers = cherrypy.response.headers
    headers["X-Frame-Options"] = "DENY"
    headers["X-XSS-Protection"] = "1; mode=block"
    headers["Content-Security-Policy"] = "default-src='self'"


class IgnoreRequestFilter(logging.Filter):
    """ Ignore requests on URL """

    def __init__(self, request_to_ignore):
        super(IgnoreRequestFilter, self).__init__()
        self.request_to_ignore = request_to_ignore

    def filter(self, record):
        return self.request_to_ignore not in record.getMessage()


class HazelcastSession(Session):
    """ Support for Hazelcast session """

    servers = ["127.0.0.1:5701"]

    def setup(cls, **kwargs):
        """ Setup. Called once """
        for k, v in kwargs.items():
            setattr(cls, k, v)
        import hazelcast
        config = hazelcast.ClientConfig()
        for server in cls.servers:
            config.network_config.addresses.append(server)
        client = hazelcast.HazelcastClient(config)
        cls.cache = client.get_map("cherrypy")

    setup = classmethod(setup)

    def _exists(self):
        return self.cache.contains_key(self.id).result()

    def _load(self):
        _data = self.cache.get(self.id).result()
        if _data is not None:
            return pickle.loads(base64.b64decode(_data))
        return _data

    def _save(self, expiration_time):
        current_time = datetime.datetime.now()
        ttl = int(abs((expiration_time - current_time).total_seconds()))
        self.cache.put(
            self.id,
            base64.b64encode(
                pickle.dumps(
                    (self._data, expiration_time),
                    pickle.HIGHEST_PROTOCOL
                )
            ),
            ttl
        ).result()

    def _delete(self):
        self.cache.remove(self.id).result()

    def acquire_lock(self):
        self.locked = True
        self.cache.lock(self.id).result()

    def release_lock(self):
        self.cache.unlock(self.id).result()
        self.locked = False

    def __len__(self):
        return self.cache.size().result()
