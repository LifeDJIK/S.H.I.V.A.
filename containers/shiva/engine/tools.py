#!/usr/bin/python
# coding=utf-8
# pylint: disable=I0011,C0103,E1101,R0201,R0903,W0702,C0111
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
    check_interval = 0.01
    max_wait_time = 0.25

    def setup(cls, **kwargs):
        """ Setup. Called once """
        for k, v in kwargs.items():
            setattr(cls, k, v)
        import socket
        socket.setdefaulttimeout(1.0)
        import hazelcast
        config = hazelcast.ClientConfig()
        config.group_config.name = "shiva"
        config.group_config.password = "shiva"
        for server in cls.servers:
            config.network_config.addresses.append(server)
        client = hazelcast.HazelcastClient(config)
        cls.cache = client.get_map("cherrypy")

    setup = classmethod(setup)

    def _exists(self):
        try:
            result = self.cache.contains_key(self.id)
            waited = 0.0
            while waited < self.max_wait_time:
                if result.done():
                    return result.result()
                time.sleep(self.check_interval)
                waited += self.check_interval
            error_text = "Wait time exceeded in _exists()"
            cherrypy.log(error_text)
            raise Exception(error_text)
        except:
            return False

    def _load(self):
        try:
            result = self.cache.get(self.id)
            waited = 0.0
            while waited < self.max_wait_time:
                if result.done():
                    _data = result.result()
                    if _data is not None:
                        _data = pickle.loads(base64.b64decode(_data))
                    return _data
                time.sleep(self.check_interval)
                waited += self.check_interval
            error_text = "Wait time exceeded in _load()"
            cherrypy.log(error_text)
            raise Exception(error_text)
        except:
            return None

    def _save(self, expiration_time):
        current_time = datetime.datetime.now()
        ttl = int(abs((expiration_time - current_time).total_seconds()))
        try:
            result = self.cache.put(
                self.id,
                base64.b64encode(
                    pickle.dumps(
                        (self._data, expiration_time),
                        pickle.HIGHEST_PROTOCOL
                    )
                ),
                ttl
            )
            waited = 0.0
            while waited < self.max_wait_time:
                if result.done():
                    result.result()
                    return
                time.sleep(self.check_interval)
                waited += self.check_interval
            error_text = "Wait time exceeded in _save()"
            cherrypy.log(error_text)
            raise Exception(error_text)
        except:
            pass

    def _delete(self):
        try:
            result = self.cache.remove(self.id)
            waited = 0.0
            while waited < self.max_wait_time:
                if result.done():
                    result.result()
                    return
                time.sleep(self.check_interval)
                waited += self.check_interval
            error_text = "Wait time exceeded in _delete()"
            cherrypy.log(error_text)
            raise Exception(error_text)
        except:
            pass

    def acquire_lock(self):
        self.locked = True
        try:
            result = self.cache.lock(self.id)
            waited = 0.0
            while waited < self.max_wait_time:
                if result.done():
                    result.result()
                    return
                time.sleep(self.check_interval)
                waited += self.check_interval
            error_text = "Wait time exceeded in acquire_lock()"
            cherrypy.log(error_text)
            raise Exception(error_text)
        except:
            pass

    def release_lock(self):
        try:
            result = self.cache.unlock(self.id)
            waited = 0.0
            while waited < self.max_wait_time:
                if result.done():
                    result.result()
                    self.locked = False
                    return
                time.sleep(self.check_interval)
                waited += self.check_interval
            error_text = "Wait time exceeded in release_lock()"
            cherrypy.log(error_text)
            raise Exception(error_text)
        except:
            self.locked = False

    def __len__(self):
        try:
            result = self.cache.size()
            waited = 0.0
            while waited < self.max_wait_time:
                if result.done():
                    return result.result()
                time.sleep(self.check_interval)
                waited += self.check_interval
            error_text = "Wait time exceeded in __len__()"
            cherrypy.log(error_text)
            raise Exception(error_text)
        except:
            return 0
